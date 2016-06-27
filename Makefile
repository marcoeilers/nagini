CHECKED_FILES:=\
							src/py2viper_translation/analyzer_io.py \
							src/py2viper_translation/translators/io_operation.py \
							src/py2viper_translation/lib/preamble_constructor.py
CHECKED_MODULES:=$(subst /,.,$(CHECKED_FILES:src/%.py=%))
BUILDOUT_DEPS=bin/buildout buildout.cfg
BUILDOUT_CMD=bin/buildout -v

test: bin/py.test
	bin/py.test -x src/py2viper_translation/tests.py

mypy: bin/mypy
	bin/mypy --fast-parser -s $(CHECKED_FILES)

flake8: bin/flake8
	bin/flake8 --ignore=F401,E501,D102 --max-complexity 12 $(CHECKED_FILES)

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
