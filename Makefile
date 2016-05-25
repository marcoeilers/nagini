test: buildout
	bin/py.test -x src/py2viper_translation/tests.py

docs: buildout
	bin/sphinxbuilder

docs_coverage: buildout
	bin/python bin/sphinx-build -b coverage docs/source docs/build/coverage

doctest: buildout
	bin/python bin/sphinx-build -b doctest docs/source docs/build/doctest

buildout: bin/buildout
	bin/buildout -v

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
