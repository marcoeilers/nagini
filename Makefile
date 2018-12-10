CHECKED_TRANSLATOR_FILES:=\
	src/nagini_translation/analyzer_io.py \
	src/nagini_translation/tests.py \
	src/nagini_translation/lib/io_context.py \
	src/nagini_translation/lib/io_checkers.py \
	src/nagini_translation/lib/guard_collectors.py \
	src/nagini_translation/lib/errors/__init__.py \
	src/nagini_translation/lib/errors/manager.py \
	src/nagini_translation/lib/errors/messages.py \
	src/nagini_translation/lib/errors/rules.py \
	src/nagini_translation/lib/errors/wrappers.py \
	src/nagini_translation/lib/obligation_context.py \
	src/nagini_translation/lib/silver_nodes/__init__.py \
	src/nagini_translation/lib/silver_nodes/base.py \
	src/nagini_translation/lib/silver_nodes/bool_expr.py \
	src/nagini_translation/lib/silver_nodes/call.py \
	src/nagini_translation/lib/silver_nodes/expression.py \
	src/nagini_translation/lib/silver_nodes/int_cmp_expr.py \
	src/nagini_translation/lib/silver_nodes/int_expr.py \
	src/nagini_translation/lib/silver_nodes/location_expr.py \
	src/nagini_translation/lib/silver_nodes/perm_cmp_expr.py \
	src/nagini_translation/lib/silver_nodes/perm_expr.py \
	src/nagini_translation/lib/silver_nodes/program.py \
	src/nagini_translation/lib/silver_nodes/reference_expr.py \
	src/nagini_translation/lib/silver_nodes/statement.py \
	src/nagini_translation/lib/silver_nodes/types.py \
	src/nagini_translation/translators/io_operation/common.py \
	src/nagini_translation/translators/io_operation/definition.py \
	src/nagini_translation/translators/io_operation/__init__.py \
	src/nagini_translation/translators/io_operation/interface.py \
	src/nagini_translation/translators/io_operation/termination_check.py \
	src/nagini_translation/translators/io_operation/use.py \
	src/nagini_translation/translators/io_operation/utils.py \
	src/nagini_translation/translators/io_operation/opener.py \
	src/nagini_translation/translators/io_operation/result_translator.py \
	src/nagini_translation/translators/obligation/__init__.py \
	src/nagini_translation/translators/obligation/common.py \
	src/nagini_translation/translators/obligation/inexhale.py \
	src/nagini_translation/translators/obligation/interface.py \
	src/nagini_translation/translators/obligation/loop.py \
	src/nagini_translation/translators/obligation/loop_node.py \
	src/nagini_translation/translators/obligation/manager.py \
	src/nagini_translation/translators/obligation/measures.py \
	src/nagini_translation/translators/obligation/method.py \
	src/nagini_translation/translators/obligation/method_call_node.py \
	src/nagini_translation/translators/obligation/method_node.py \
	src/nagini_translation/translators/obligation/node_constructor.py \
	src/nagini_translation/translators/obligation/obligation_info.py \
	src/nagini_translation/translators/obligation/utils.py \
	src/nagini_translation/translators/obligation/types/__init__.py \
	src/nagini_translation/translators/obligation/types/base.py \
	src/nagini_translation/translators/obligation/types/must_invoke.py \
	src/nagini_translation/translators/obligation/types/must_release.py \
	src/nagini_translation/translators/obligation/types/must_terminate.py \
	src/nagini_translation/translators/obligation/waitlevel.py
CHECKED_CONTRACT_FILES:=\
	src/nagini_contracts/io.py \
	src/nagini_contracts/io_builtins.py \
	src/nagini_contracts/obligations.py \
	src/nagini_contracts/lock.py

CHECKED_FILES=$(CHECKED_TRANSLATOR_FILES) $(CHECKED_CONTRACT_FILES)

CHECKED_MODULES:=$(subst /,.,$(CHECKED_FILES:src/%.py=%))

DEPS=env
CMD=env

.PHONY: docs

test: env/bin/py.test
	env/bin/pytest -v src/nagini_translation/tests.py

freeze: env
	env/bin/pip freeze > requirements.txt

mypy: env/bin/mypy
	MYPYPATH=stubs:src env/bin/mypy --fast-parser -s $(CHECKED_FILES)

flake8: env/bin/flake8
	env/bin/flake8 --ignore=F401,F403,E501,D102,D105 --max-complexity 12 $(CHECKED_FILES)

pylint: env/bin/pylint
	env/bin/pylint $(CHECKED_MODULES)

pylint_silent: env/bin/pylint
	env/bin/pylint --disable=I $(CHECKED_MODULES)

pylint_report: env/bin/pylint
	env/bin/pylint --reports=y $(CHECKED_MODULES)

# TODO: Fix.
docs: env/bin/sphinxbuilder
	bash env/bin/sphinxbuilder

# TODO: Fix.
docs_coverage: env/bin/python env/bin/sphinx-build
	env/bin/python env/bin/sphinx-build -b coverage docs/source docs/build/coverage

# TODO: Fix.
doctest: env/bin/python env/bin/sphinx-build
	env/bin/python env/bin/sphinx-build -b doctest docs/source docs/build/doctest

env/bin/py.test: $(DEPS)

env/bin/mypy: $(DEPS)

env/bin/flake8: $(DEPS)

env/bin/pylint: $(DEPS)

env/bin/sphinxbuilder: $(DEPS)

env/bin/sphinx-build: $(DEPS)

env/bin/python: $(DEPS)

env: .virtualenv
	python3 .virtualenv/source/virtualenv.py env
	env/bin/pip install -r requirements.txt
	env/bin/pip install -e .

.virtualenv:
	mkdir -p .virtualenv
	wget -c \
		https://pypi.python.org/packages/d4/0c/9840c08189e030873387a73b90ada981885010dd9aea134d6de30cd24cb8/virtualenv-15.1.0.tar.gz#md5=44e19f4134906fe2d75124427dc9b716 \
		-O .virtualenv/archive.tar.gz
	tar -xvf .virtualenv/archive.tar.gz
	mv virtualenv-* .virtualenv/source

clean:
	rm -rf \
		.virtualenv bin deps/JPype1 develop-eggs env parts \
		.installed.cfg .mr.developer.cfg tmp
