Making a new release
--------------------

1. For a new major release, remove stuff (e.g. parameters, methods) deprecated in the previous cycle
2. Update the `__version__` string in `bioblend/__init__.py`
3. Update `CHANGELOG.md`
4. Commit the changes above, push to GitHub, and wait for integration tests to pass on TravisCI
5. Make a release through the GitHub interface
6. Run `make release` to upload to PyPI
7. Optionally update the [Bioconda package](https://github.com/bioconda/bioconda-recipes/blob/master/recipes/bioblend/meta.yaml)
