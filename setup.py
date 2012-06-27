from setuptools import setup

from blend import __version__

setup(name = "blend",
      version = __version__,
      description = "BioCloudCentral, CloudMan, and Galaxy Library",
      author = "Enis Afgan",
      author_email = "afgane@gmail.com",
      url = "https://github.com/afgane/blend",
      install_requires = ['requests', 'simplejson', 'boto'],
      packages = ['blend', 'blend.bcc', 'blend.cloudman', 'blend.galaxy',
                  'blend.galaxy.datasets', 'blend.galaxy.histories',
                  'blend.galaxy.libraries', 'blend.galaxy.users',
                  'blend.galaxy.workflows'],
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
