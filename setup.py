# http://bugs.python.org/issue15881#msg170215
try:
    import multiprocessing
except ImportError:
    pass

import sys

from setuptools import setup, find_packages

from bioblend import get_version

tests_require = ['mock>=0.7.0', 'nose>=1.3.1']
if sys.version_info < (2, 7):
    tests_require.append('unittest2>=0.5.1')

setup(name="bioblend",
      version=get_version(),
      description="CloudMan and Galaxy API library",
      author="Enis Afgan",
      author_email="afgane@gmail.com",
      url="http://bioblend.readthedocs.org/",
      install_requires=['requests>=1.1.0', 'poster', 'boto>=2.9.7', 'pyyaml'],
      tests_require=tests_require,
      packages=find_packages(),
      license='MIT',
      platforms="Posix; MacOS X; Windows",
      classifiers=["Development Status :: 3 - Alpha",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: MIT License",
                   "Operating System :: OS Independent",
                   "Topic :: Internet",
                   "Programming Language :: Python :: 2",
                   "Programming Language :: Python :: 2.6",
                   "Programming Language :: Python :: 2.7"],
      test_suite='nose.collector',
      )
