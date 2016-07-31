"""Code for constructing Silver Method nodes with obligation stuff."""


from py2viper_translation.lib import expressions as expr
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
    PythonVar,
)
from py2viper_translation.lib.typedefs import (
    Info,
    Method,
    Position,
)
from py2viper_translation.lib.viper_ast import ViperAST
from py2viper_translation.translators.obligation.obligation_info import (
    PythonMethodObligationInfo,
)


class ObligationMethod:
    """Info for generating Silver ``Method`` AST node."""

    def __init__(self, name, args, returns, pres, posts,
                 local_vars, body) -> None:
        self.name = name
        self.args = args
        self.returns = returns
        self.pres = pres
        self.posts = posts
        self.local_vars = local_vars
        self.body = body

    def prepend_args(self, args) -> None:
        """Prepend ``args`` to the argument list."""
        self.args = args + self.args

    def prepend_body(self, statements) -> None:
        """Prepend ``statements`` to body."""
        self.body = statements + self.body

    def prepend_precondition(self, preconditions) -> None:
        """Prepend ``preconditions`` to precondition list."""
        self.pres = preconditions + self.pres

    def add_local(self, var: PythonVar) -> None:
        """Add local variable to variables list."""
        self.local_vars.append(var.decl)


class ObligationsMethodNodeConstructor:
    """A class that creates a method node with obligation stuff."""

    def __init__(
            self, obligation_method: ObligationMethod,
            python_method: PythonMethod, translator: 'AbstractTranslator',
            ctx: Context, position: Position, info: Info) -> None:
        self._obligation_method = obligation_method
        self._python_method = python_method
        self._translator = translator
        self._ctx = ctx
        self._position = position
        self._info = info

    def construct_node(self) -> Method:
        """Construct a Silver node that represents a method."""
        method = self._obligation_method
        body = method.body
        if self._is_body_native_silver():
            # Axiomatized method, do nothing with body.
            body_block = body
        else:
            # Convert body to Scala.
            body_block = self._translator.translate_block(
                body, self._position, self._info)
        return self._viper.Method(
            method.name, method.args, method.returns,
            method.pres, method.posts, method.local_vars, body_block,
            self._position, self._info)

    def add_obligations(self) -> None:
        """Add obligation stuff to Method."""
        self._add_aditional_parameters()
        self._add_additional_preconditions()
        if not self._need_skip_body():
            self._set_up_measures()
            self._add_book_keeping_vars()
        # TODO: self._add_leak_check()
        # TODO: Finish implementation.

    def _is_body_native_silver(self) -> bool:
        """Check if body is already in Silver."""
        return isinstance(
            self._obligation_method.body,
            self._translator.jvm.viper.silver.ast.Seqn)

    def _need_skip_body(self) -> bool:
        """Check if altering body should not be done."""
        return (self._is_body_native_silver() or
                self._python_method.contract_only)

    def _add_aditional_parameters(self) -> None:
        """Add current thread and caller measures parameters."""
        self._obligation_method.prepend_args([
            self._obligation_info.current_thread_var.decl,
            self._obligation_info.caller_measure_map.get_var().decl,
        ])

    def _add_additional_preconditions(self) -> None:
        """Add preconditions about current thread and caller measures."""
        cthread = expr.VarRef(self._obligation_info.current_thread_var)
        measure_map = self._obligation_info.caller_measure_map
        measures = expr.VarRef(measure_map.get_var())
        preconditions = [
            cthread != None,        # noqa: E711
            measures != None,       # noqa: E711
            measure_map.get_contents_access(),
        ]
        self._obligation_method.prepend_precondition([
            precondition.translate(
                self._translator, self._ctx, self._position, self._info)
            for precondition in preconditions])

    def _set_up_measures(self) -> None:
        """Create and initialize method's measure map."""
        instances = self._obligation_info.get_all_precondition_instances()
        statements = self._obligation_info.method_measure_map.initialize(
            instances, self._translator, self._ctx)
        self._obligation_method.prepend_body(statements)
        self._obligation_method.add_local(
            self._obligation_info.method_measure_map.get_var())
        self._obligation_method.add_local(
            self._obligation_info.method_measure_map.get_contents_var())

    def _add_book_keeping_vars(self) -> None:
        self._obligation_method.add_local(
            self._obligation_info.original_must_terminate_var)
        self._obligation_method.add_local(
            self._obligation_info.increased_must_terminate_var)

    @property
    def _obligation_info(self) -> PythonMethodObligationInfo:
        return self._python_method.obligation_info

    @property
    def _viper(self) -> ViperAST:
        return self._translator.viper
