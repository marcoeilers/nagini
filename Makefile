CHECKED_TRANSLATOR_FILES:=\
	src/py2viper_translation/analyzer_io.py \
	src/py2viper_translation/lib/preamble_constructor.py \
	src/py2viper_translation/lib/io_context.py \
	src/py2viper_translation/lib/io_checkers.py \
	src/py2viper_translation/lib/guard_collectors.py \
	src/py2viper_translation/lib/expressions.py \
	src/py2viper_translation/lib/errors/__init__.py \
	src/py2viper_translation/lib/errors/manager.py \
	src/py2viper_translation/lib/errors/messages.py \
	src/py2viper_translation/lib/errors/rules.py \
	src/py2viper_translation/lib/errors/wrappers.py \
	src/py2viper_translation/lib/obligation_context.py \
	src/py2viper_translation/translators/io_operation/common.py \
	src/py2viper_translation/translators/io_operation/definition.py \
	src/py2viper_translation/translators/io_operation/__init__.py \
	src/py2viper_translation/translators/io_operation/interface.py \
	src/py2viper_translation/translators/io_operation/termination_check.py \
	src/py2viper_translation/translators/io_operation/use.py \
	src/py2viper_translation/translators/io_operation/utils.py \
	src/py2viper_translation/translators/io_operation/opener.py \
	src/py2viper_translation/translators/io_operation/result_translator.py \
	src/py2viper_translation/translators/obligation/__init__.py \
	src/py2viper_translation/translators/obligation/common.py \
	src/py2viper_translation/translators/obligation/interface.py \
	src/py2viper_translation/translators/obligation/loop.py \
	src/py2viper_translation/translators/obligation/loop_node.py \
	src/py2viper_translation/translators/obligation/manager.py \
	src/py2viper_translation/translators/obligation/measures.py \
	src/py2viper_translation/translators/obligation/method.py \
	src/py2viper_translation/translators/obligation/method_call_node.py \
	src/py2viper_translation/translators/obligation/method_node.py \
	src/py2viper_translation/translators/obligation/node_constructor.py \
	src/py2viper_translation/translators/obligation/obligation_info.py \
	src/py2viper_translation/translators/obligation/utils.py \
	src/py2viper_translation/translators/obligation/types/__init__.py \
	src/py2viper_translation/translators/obligation/types/base.py \
	src/py2viper_translation/translators/obligation/types/must_terminate.py
CHECKED_CONTRACT_FILES:=\
	deps/py2viper-contracts/src/py2viper_contracts/io.py \
	deps/py2viper-contracts/src/py2viper_contracts/io_builtins.py \
	deps/py2viper-contracts/src/py2viper_contracts/obligations.py

CHECKED_FILES=$(CHECKED_TRANSLATOR_FILES) $(CHECKED_CONTRACT_FILES)

CHECKED_TRANSLATOR_MODULES:=$(subst /,.,$(CHECKED_TRANSLATOR_FILES:src/%.py=%))
CHECKED_CONTRACT_MODULES:=$(subst /,.,$(CHECKED_CONTRACT_FILES:deps/py2viper-contracts/src/%.py=%))
CHECKED_MODULES:=$(CHECKED_TRANSLATOR_MODULES) $(CHECKED_CONTRACT_MODULES)

BUILDOUT_DEPS=bin/buildout buildout.cfg
BUILDOUT_CMD=bin/buildout -v

test: bin/py.test
	bin/py.test -v -x src/py2viper_translation/tests.py

mypy: bin/mypy
	MYPYPATH=stubs:deps/py2viper-contracts/src bin/mypy --fast-parser -s $(CHECKED_FILES)

flake8: bin/flake8
	bin/flake8 --ignore=F401,E501,D102,D105 --max-complexity 12 $(CHECKED_FILES)

pylint: bin/pylint
	bin/pylint $(CHECKED_MODULES)

pylint_report: bin/pylint
	bin/pylint --reports=y $(CHECKED_MODULES)

docs: bin/sphinxbuilder
	bin/sphinxbuilder

docs_coverage: bin/python bin/sphinx-build
	bin/python bin/sphinx-build -b coverage docs/source docs/build/coverage

doctest: bin/python bin/sphinx-build
	bin/python bin/sphinx-build -b doctest docs/source docs/build/doctest

bin/py.test: $(BUILDOUT_DEPS)
	$(BUILDOUT_CMD)

bin/mypy: $(BUILDOUT_DEPS)
	$(BUILDOUT_CMD)

bin/flake8: $(BUILDOUT_DEPS)
	$(BUILDOUT_CMD)

bin/pylint: $(BUILDOUT_DEPS)
	$(BUILDOUT_CMD)

bin/sphinxbuilder: $(BUILDOUT_DEPS)
	$(BUILDOUT_CMD)

bin/sphinx-build: $(BUILDOUT_DEPS)
	$(BUILDOUT_CMD)

bin/python: $(BUILDOUT_DEPS)
	$(BUILDOUT_CMD)

buildout: $(BUILDOUT_DEPS)
	$(BUILDOUT_CMD)

bin/buildout: bootstrap.py env deps/py2viper-contracts
	env/bin/python bootstrap.py

deps/py2viper-contracts:
	mkdir -p deps
	hg clone ssh://hg@bitbucket.org/viperproject/py2viper-contracts deps/py2viper-contracts

env: .virtualenv
	python3 .virtualenv/source/virtualenv.py env

.virtualenv:
	mkdir -p .virtualenv
	wget -c \
		https://pypi.python.org/packages/c8/82/7c1eb879dea5725fae239070b48187de74a8eb06b63d9087cd0a60436353/virtualenv-15.0.1.tar.gz \
		-O .virtualenv/archive.tar.gz
	tar -xvf .virtualenv/archive.tar.gz
	mv virtualenv-* .virtualenv/source

clean:
	rm -rf \
		.virtualenv bin deps/JPype1 develop-eggs env parts \
		.installed.cfg .mr.developer.cfg tmp
