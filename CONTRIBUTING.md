Making a new release
--------------------

1. For a new major release, remove stuff (e.g. parameters, methods) deprecated in the previous cycle.
2. Update the `__version__` string in `bioblend/__init__.py` .
3. Update `CHANGELOG.md` .
4. Commit the changes above, push to GitHub, and wait for Continuous Integration (CI) tests to pass.
5. Make a new release through the GitHub interface. A CI job will automatically upload the packages to PyPI.
7. Optionally update the [Bioconda package](https://github.com/bioconda/bioconda-recipes/blob/master/recipes/bioblend/meta.yaml).
