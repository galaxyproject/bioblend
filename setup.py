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
if sys.version_info < (2, 7):
    tests_require.extend(['mock>=0.7.0,<=1.0.1', 'unittest2>=0.5.1'])
elif sys.version_info < (3, 3):
    tests_require.append('mock>=0.7.0')

ENTRY_POINTS = '''
    [console_scripts]
    bioblend-galaxy-tests=bioblend._tests.pytest_galaxy_test_wrapper:main
'''

setup(name="bioblend",
      version=version,
      description="CloudMan and Galaxy API library",
      author="Enis Afgan",
      author_email="afgane@gmail.com",
      url="http://bioblend.readthedocs.org/",
      install_requires=['requests>=2.4.3,!=2.12.0,!=2.12.1', 'requests-toolbelt', 'boto>=2.9.7', 'pyyaml', 'six'],
      tests_require=tests_require,
      packages=find_packages(exclude=['tests']),
      entry_points=ENTRY_POINTS,
      extras_require={
          'testing': ["pytest"],
      },
      license='MIT',
      platforms="Posix; MacOS X; Windows",
      classifiers=["Development Status :: 4 - Beta",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: MIT License",
                   "Operating System :: OS Independent",
                   "Topic :: Scientific/Engineering",
                   "Programming Language :: Python :: 2",
                   "Programming Language :: Python :: 2.6",
                   "Programming Language :: Python :: 2.7",
                   "Programming Language :: Python :: 3",
                   "Programming Language :: Python :: 3.3",
                   "Programming Language :: Python :: 3.4",
                   "Programming Language :: Python :: 3.5",
                   "Programming Language :: Python :: 3.6"],
      test_suite='nose.collector')
