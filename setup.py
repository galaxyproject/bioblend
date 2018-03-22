import ast
import os.path
import re
import sys

from setuptools import find_packages, setup

# Cannot use "from bioblend import get_version" because that would try to import
# the six package which may not be installed yet.
reg = re.compile(r'__version__\s*=\s*(.+)')
with open(os.path.join('bioblend', '__init__.py')) as f:
    for line in f:
        m = reg.match(line)
        if m:
            version = ast.literal_eval(m.group(1))
            break

tests_require = ['nose>=1.3.1']
if sys.version_info < (3, 3):
    tests_require.append('mock>=0.7.0')

setup(
    name="bioblend",
    version=version,
    description="CloudMan and Galaxy API library",
    long_description=open('README.rst').read(),
    author="Enis Afgan",
    author_email="afgane@gmail.com",
    url="https://bioblend.readthedocs.io/",
    install_requires=[
        'boto>=2.9.7',
        'pyyaml',
        'requests>=2.4.3,!=2.12.0,!=2.12.1',
        'requests-toolbelt',
        'six'
    ],
    tests_require=tests_require,
    packages=find_packages(exclude=['tests']),
    package_data={'bioblend': ['_tests/data/*']},
    entry_points={
        'console_scripts': [
            'bioblend-galaxy-tests = bioblend._tests.pytest_galaxy_test_wrapper:main [testing]'
        ]
    },
    extras_require={
        'testing': ["pytest"],
    },
    license='MIT',
    platforms="Posix; MacOS X; Windows",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Scientific/Engineering",
    ],
    test_suite='nose.collector')
