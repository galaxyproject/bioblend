from setuptools import setup

from bioblend import get_version

setup(name = "bioblend",
      version = get_version(),
      description = "CloudMan and Galaxy API library",
      author = "Enis Afgan",
      author_email = "afgane@gmail.com",
      url = "http://bioblend.readthedocs.org/",
      install_requires = ['requests', 'poster', 'simplejson', 'boto', 'nose', 'mock', 'pyyaml'],
      packages = ['bioblend', 'bioblend.cloudman', 'bioblend.galaxy', 'bioblend.util',
                  'bioblend.galaxy.datasets', 'bioblend.galaxy.histories',
                  'bioblend.galaxy.libraries', 'bioblend.galaxy.users',
                  'bioblend.galaxy.workflows'],
      license = 'MIT',
      platforms = "Posix; MacOS X; Windows",
      classifiers = ["Development Status :: 3 - Alpha",
                     "Intended Audience :: Developers",
                     "License :: OSI Approved :: MIT License",
                     "Operating System :: OS Independent",
                     "Topic :: Internet",
                     "Programming Language :: Python :: 2",
                     "Programming Language :: Python :: 2.6",
                     "Programming Language :: Python :: 2.7"],
)
