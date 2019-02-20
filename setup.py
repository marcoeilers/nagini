#!/usr/bin/env python3

from setuptools import setup, find_packages


setup(
        name='nagini',
        version='0.8',
        author='Viper Team',
        author_email='viper@inf.ethz.ch',
        license='MPL-2.0',
        packages=find_packages('src'),
        package_dir={'': 'src'},
        requires=[
            'distribute',
            ],
        install_requires=[
            'mypy-lang',
            'toposort',
            'jpype1',
            'astunparse',
            'typed-ast',
            'pyzmq',
            ],
        entry_points = {
             'console_scripts': [
                 'nagini = nagini_translation.main:main',
                 ]
             },
        url='http://www.pm.inf.ethz.ch/research/nagini.html',
        description='Static verifier for Python 3, based on Viper.',
        # Full list of classifiers could be found at:
        # http://pypi.python.org/pypi?%3Aaction=list_classifiers
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3 :: Only',
            'Topic :: Software Development',
            ],
        )
