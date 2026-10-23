"""
Copyright (c) 2026 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


import jpype
import logging

from typing import List

from nagini_translation.lib.jvmaccess import configure_java_logging, getobject, JVM
from nagini_translation.lib.util import list_to_seq
# Re-exported so the service can build backend args without importing verifier
# directly; verifier.py is the single source of truth for these.
from nagini_translation.verifier import (
    build_carbon_backend_args,
    build_silicon_backend_args,
    Failure,
    get_arp_plugin,
    Success,
    VerificationResult,
)


class ViperServerManager:
    """
    Wraps a single, long-lived ``viper.server.core.ViperCoreServer`` instance.

    The server is started lazily and reused across verification requests so
    that ViperServer's result caching survives between requests (e.g. in
    Nagini's ``--server`` mode). It also provides hooks for cancelling running
    jobs and flushing the cache, which a future LSP/MCP frontend can drive.
    """

    def __init__(self, jvm: JVM):
        self.jvm = jvm
        self.server = None
        self.executor = None
        self._started = False
        # Optional path for ViperServer's journal (its --logFile). When unset,
        # ViperServer writes to a throwaway temp file, which is lost with the
        # environment (e.g. a container's /tmp) — set this before the first
        # verification to keep backend exception details diagnosable.
        self.log_file = None

    def start(self) -> None:
        if self._started:
            return
        jvm = self.jvm
        if not jvm.is_known_class(jvm.viper.server.frontends.lsp, 'ViperServerService'):
            raise Exception('ViperServer not found on classpath.')
        self._configure_logging()
        # Server-level configuration (ScallopConf parsed from CLI-style args).
        # A high job limit lets several verifications run concurrently.
        args = ['--logLevel', 'ERROR', '--maximumActiveJobs', '1024']
        if self.log_file:
            args += ['--logFile', self.log_file]
        server_args = list_to_seq(args, jvm, jvm.java.lang.String)
        cfg = jvm.viper.server.ViperConfig(server_args)
        # Execution context with the library's default actor-system/thread-pool
        # settings (None => automatic thread count).
        none = getobject(jvm.java, jvm.scala, 'None')
        self.executor = jvm.viper.server.core.DefaultVerificationExecutionContext(
            'nagini', 'nagini-viper-server', none)
        # ViperCoreServer is abstract; Gobra instantiates it as
        # `new ViperCoreServer(...) with DefaultVerificationServerStart`, an
        # anonymous mixin that cannot be expressed through JPype. ViperServerService
        # is the concrete class `ViperCoreServer with DefaultVerificationServerStart`
        # and, unlike ViperHttpServer, binds no network port; we use it purely for
        # its inherited verify/getResultsFuture/flushCache/stop API.
        self.server = jvm.viper.server.frontends.lsp.ViperServerService(cfg, self.executor)
        self._await(self.server.start(), timeout_ms=120000)
        self._started = True

    @property
    def started(self) -> bool:
        return self._started

    def _configure_logging(self) -> None:
        # viperserver.jar ships no logback.xml, so logback defaults to DEBUG on
        # the console, flooding output with internal Silicon traces. Raise the
        # root log level so only warnings and errors are shown. This normally
        # already happened when the JVM was created (see
        # jvmaccess.configure_java_logging); we repeat it here defensively in
        # case the server is driven on a JVM started elsewhere.
        configure_java_logging()

    def _duration(self, timeout_ms=None):
        jvm = self.jvm
        if timeout_ms is None:
            return jvm.scala.concurrent.duration.Duration.Inf()
        return jvm.scala.concurrent.duration.Duration.create(
            timeout_ms, jvm.java.util.concurrent.TimeUnit.MILLISECONDS)

    def _await(self, future, timeout_ms=None):
        """Block until the given Scala Future completes and return its value.

        A ``timeout_ms`` of ``None`` waits indefinitely (used for verification,
        which may legitimately take a long time); a finite value is used for
        lifecycle operations so they can never hang the process.
        """
        return self.jvm.scala.concurrent.Await.result(future, self._duration(timeout_ms))

    def submit(self, prog, program_id: str, backend_args: List[str],
               backend: str = 'silicon'):
        """Submit an in-memory program for verification; returns a VerJobId.

        ``backend`` selects the Viper backend (``'silicon'`` or ``'carbon'``).
        """
        none = getobject(self.jvm.java, self.jvm.scala, 'None')
        args_list = list_to_seq(backend_args, self.jvm,
                                self.jvm.java.lang.String).toList()
        if backend == 'carbon':
            backend_cfg = self.jvm.viper.server.core.CarbonConfig.apply(args_list)
        else:
            backend_cfg = self.jvm.viper.server.core.SiliconConfig.apply(args_list)
        return self.server.verify(program_id, backend_cfg, prog, none)

    def result_future(self, job_id):
        return self.jvm.viper.server.core.ViperCoreServerUtils.getResultsFuture(
            self.server, job_id, self.executor)

    def await_result(self, job_id, timeout_ms=None):
        """Block (concurrently across jobs) until ``job_id``'s result is ready.

        With a finite ``timeout_ms`` the wait raises
        ``java.util.concurrent.TimeoutException`` once it elapses; the caller is
        then responsible for cancelling the job (the job itself keeps running).
        """
        return self._await(self.result_future(job_id), timeout_ms=timeout_ms)

    def messages_future(self, job_id):
        return self.jvm.viper.server.core.ViperCoreServerUtils.getMessagesFuture(
            self.server, job_id, self.executor)

    def await_messages(self, job_id, timeout_ms=None):
        """Block until ``job_id``'s message stream completes; returns the
        Scala ``List[Message]`` of everything the job reported.

        Unlike ``await_result`` (whose future *asserts* that the stream holds
        exactly one overall success/failure message and hence fails uselessly
        for jobs that died or were cancelled), this completes with the partial
        stream in every case, letting the caller classify the outcome — an
        overall result message, an ``ExceptionReport`` (backend crash), or
        neither (cancellation). Timeout semantics are as in ``await_result``.
        """
        return self._await(self.messages_future(job_id), timeout_ms=timeout_ms)

    def cancel_job(self, job_id) -> None:
        """Precisely stop a single running job by sending its actor StopVerification."""
        if not self._started:
            return
        try:
            pool = self.server.ver_jobs()
            opt = pool.lookupJob(job_id)
            if opt is None or not opt.isDefined():
                return
            handle = self._await(opt.get(), timeout_ms=5000)
            stop = getobject(self.jvm.java, self.jvm.viper.server.vsi,
                             'VerificationProtocol$StopVerification')
            no_sender = jpype.JClass('akka.actor.ActorRef').noSender()
            handle.job_actor().tell(stop, no_sender)
            pool.discardJob(job_id)
        except Exception:
            logging.exception('Error cancelling ViperServer job.')

    def flush_cache(self) -> None:
        if self._started:
            none = getobject(self.jvm.java, self.jvm.scala, 'None')
            self.server.flushCache(none)

    def cancel_all(self) -> None:
        """Interrupt all running verification jobs."""
        if self._started:
            self._await(self.server.getInterruptFutureList())

    def stop(self) -> None:
        if not self._started:
            return
        try:
            if self.server is not None:
                self._await(self.server.stop(), timeout_ms=15000)
        except Exception:
            logging.exception('Error while stopping ViperServer.')
        # Terminate the Akka actor system / thread pool, otherwise its
        # non-daemon threads keep the JVM (and hence the process) alive.
        try:
            if self.executor is not None:
                default = getattr(self.executor, 'terminate$default$1')()
                self.executor.terminate(default)
        except Exception:
            logging.exception('Error while terminating ViperServer executor.')
        self._started = False


_MANAGER = None


def get_viper_server_manager(jvm: JVM) -> ViperServerManager:
    """Return the process-wide :class:`ViperServerManager`, creating it lazily."""
    global _MANAGER
    if _MANAGER is None:
        _MANAGER = ViperServerManager(jvm)
    return _MANAGER


class ViperServer:
    """
    Provides access to the Silicon backend through ViperServer.

    Mirrors the interface of :class:`nagini_translation.verifier.Silicon` so it
    can be used interchangeably, but submits the in-memory Viper program to a
    shared, long-lived ViperServer instance (enabling caching and cancellation)
    and awaits the result via ``ViperCoreServerUtils.getResultsFuture``, which
    yields the same ``viper.silver.verifier.VerificationResult`` that the direct
    backend produces.
    """

    def __init__(self, jvm: JVM, manager: ViperServerManager, filename: str,
                 viper_args: List[str], counterexample: bool,
                 disable_branch_conditions: bool, backend: str = 'silicon'):
        self.jvm = jvm
        self.silver = jvm.viper.silver
        self.manager = manager
        self.filename = filename
        self.backend = backend
        manager.start()
        # The exact same command line as the corresponding direct backend, so
        # that verification behaviour matches.
        if backend == 'carbon':
            self.backend_args = build_carbon_backend_args(viper_args)
        else:
            self.backend_args = build_silicon_backend_args(
                viper_args, counterexample, disable_branch_conditions)

    def verify(self, modules, prog: 'silver.ast.Program', arp=False,
               sif=False) -> VerificationResult:
        """
        Verifies the given program using the selected backend via ViperServer.
        """
        jvm = self.jvm
        # A stable program id makes ViperServer's cache keys line up across
        # repeated verifications of the same file.
        program_id = self.filename or 'nagini_program'
        job_id = self.manager.submit(prog, program_id, self.backend_args,
                                     backend=self.backend)
        result = self.manager.await_result(job_id)
        if arp:
            result = get_arp_plugin(jvm).map_result(result)
        if isinstance(result, self.silver.verifier.Failure):
            it = result.errors().toIterator()
            errors = []
            while it.hasNext():
                errors += [it.next()]
            return Failure(errors, jvm, modules, sif)
        else:
            return Success()

    def stop(self):
        # The underlying server is long-lived and owned by the manager, so a
        # per-verification stop is a no-op.
        pass
