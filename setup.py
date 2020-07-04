import ast
import os.path
import re

from setuptools import find_packages, setup

# It should be possible to use "from bioblend import get_version", but this may
# try to import some not-yet-installed libraries.
reg = re.compile(r'__version__\s*=\s*(.+)')
with open(os.path.join('bioblend', '__init__.py')) as f:
    for line in f:
        m = reg.match(line)
        if m:
            version = ast.literal_eval(m.group(1))
            break
with open('README.rst') as f:
    long_description = f.read()

setup(
    name="bioblend",
    version=version,
    description="CloudMan and Galaxy API library",
    long_description=long_description,
    author="Enis Afgan",
    author_email="afgane@gmail.com",
    url="https://bioblend.readthedocs.io/",
    project_urls={
        "Bug Tracker": "https://github.com/galaxyproject/bioblend/issues",
        "Documentation": "https://bioblend.readthedocs.io/",
        "Source Code": "https://github.com/galaxyproject/bioblend",
    },
    python_requires='>=3.5',
    install_requires=[
        'boto>=2.9.7',
        'pyyaml',
        'requests>=2.20.0',
        'requests-toolbelt>=0.5.1,!=0.9.0',
    ],
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
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Scientific/Engineering",
    ]
)
