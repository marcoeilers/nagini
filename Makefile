test: buildout
	bin/py.test -x tests.py

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
		https://pypi.python.org/packages/source/v/virtualenv/virtualenv-14.0.5.tar.gz \
		-O .virtualenv/archive.tar.gz
	tar -xvf .virtualenv/archive.tar.gz
	mv virtualenv-* .virtualenv/source
