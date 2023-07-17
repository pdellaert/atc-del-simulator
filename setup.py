#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'click>=7.0',
    'rich>=13.0',
    'rich-click>=1.6',
    'requests>=2.31',
    'loguru>=0.7'
]

test_requirements = [ ]

setup(
    author="Philippe Dellaert",
    author_email='philippe@dellaert.org',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
    ],
    description="A tool to practice ATC Clearance Delivery phraseology based on data from FlightAware of real flights.",
    entry_points={
        'console_scripts': [
            'atc-del-simulator=atc_del_simulator.cli:cli',
        ],
    },
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='atc-del-simulator',
    name='atc-del-simulator',
    packages=find_packages(include=['atc_del_simulator', 'atc_del_simulator.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/pdellaert/atc-del-simulator',
    version='0.1.0',
    zip_safe=False,
)
