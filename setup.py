#!/usr/bin/env python3

from distutils.core import setup


setup(
        name='nagini',
        version='0.1',
        author='Viper Team',
        author_email='viper@inf.ethz.ch',
        packages=['nagini_translation',],
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
        url='http://www.pm.inf.ethz.ch/research/viper.html',
        description='Python frontend for VIPER.',
        long_description=(open('README.rst').read()),
        # Full list of classifiers could be found at:
        # http://pypi.python.org/pypi?%3Aaction=list_classifiers
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Console',
            'Intended Audience :: Developers',
            # TODO: License? 
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3 :: Only',
            'Topic :: Software Development',
            ],
        #TODO: license=
        )
