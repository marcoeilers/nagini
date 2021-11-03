"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from setuptools import setup, find_packages


setup(
        name='nagini',
        version='0.9.0',
        author='Viper Team',
        author_email='viper@inf.ethz.ch',
        license='MPL-2.0',
        packages=find_packages('src'),
        package_dir={'': 'src'},
        package_data={
            '': ['*.sil', '*.index', '*.typed'],
            'nagini_translation.resources': ['backends/*.jar']
        },
        requires=[
            'distribute',
            ],
        install_requires=[
            'mypy==0.782',
            'toposort==1.5',
            'jpype1==0.7.0',
            'astunparse==1.6.2',
            'typed-ast==1.4.0',
            'pytest==4.3.0',
            'pytest-xdist==1.27.0',
            'z3-solver==4.8.7.0'
            ],
        entry_points = {
             'console_scripts': [
                 'nagini = nagini_translation.main:main',
                 ]
             },
        url='http://www.pm.inf.ethz.ch/research/nagini.html',
        description='Static verifier for Python 3, based on Viper.',
        long_description=(open('README.rst').read()),
        # Full list of classifiers could be found at:
        # http://pypi.python.org/pypi?%3Aaction=list_classifiers
        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3 :: Only',
            'Topic :: Software Development',
            ],
        )
