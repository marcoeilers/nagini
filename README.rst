Getting Started (Ubuntu Linux only)
===================================

1.  `Install Viper <https://bitbucket.org/viperproject/documentation/wiki/Home#markdown-header-binary-packages-ubuntu-linux-only>`_.
2.  Clone repository::

        hg clone https://bitbucket.org/viperproject/py2viper-translation

3.  Install dependencies and run tests::

        make test

If fails with error::

    subprocess.CalledProcessError: Command '['curl', 'https://pypi.python.org/packages/source/s/setuptools/setuptools-20.2.2.zip', '--silent', '--output', '/tmp/bootstrap-mbuvyhif/setuptools-20.2.2.zip']' returned non-zero exit status 77
    make: *** [bin/buildout] Error 1

Try to set::

    export CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

Known Issues
============

``mypy-lang`` is downloaded from different source because of
`this issue <https://github.com/python/mypy/issues/1252>`_.
