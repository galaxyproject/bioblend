Making a new release
--------------------

1. For a new major release, remove stuff (e.g. parameters, methods) deprecated in the previous cycle.
2. Update the `__version__` string in `bioblend/__init__.py` .
3. Update `CHANGELOG.md` .
4. Commit the changes above, push to GitHub, and wait for Continuous Integration (CI) tests to pass.
5. Make a new release through the GitHub interface. A CI job will automatically upload the packages to PyPI.
7. Check and merge the automatic pull request to update the [Bioconda package](https://github.com/bioconda/bioconda-recipes/blob/master/recipes/bioblend/meta.yaml).

How to run BioBlend tests
-------------------------

1. Clone Galaxy to a directory outside of BioBlend source directory via `git clone https://github.com/galaxyproject/galaxy.git`

2. Change directory to your BioBlend source and run the tests via `./run_bioblend_tests.sh -g GALAXY_PATH [-r GALAXY_REV] [-e TOX_ENV]` where `GALAXY_PATH` is the directory where the galaxy repository was cloned, `GALAXY_REV` is the branch or commit of Galaxy that you would like to test against (if different from the current state of your galaxy clone), and `TOX_ENV` is used to specify the Python version to use for BioBlend, e.g. `py38` for Python 3.8.

   You can also add `2>&1 | tee log.txt` to the command above to contemporarily view the test output and save it to the `log.txt` file.

3. If needed, you can temporarily increase the Galaxy job timeout used by BioBlend tests with e.g. `export BIOBLEND_TEST_JOB_TIMEOUT=100`, and re-run the tests.
