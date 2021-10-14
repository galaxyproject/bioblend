Making a new release
--------------------

1. For a new major release, remove stuff (e.g. parameters, methods) deprecated in the previous cycle.
2. Update the `__version__` string in `bioblend/__init__.py` .
3. Update `CHANGELOG.md` .
4. Commit the changes above, push to GitHub, and wait for Continuous Integration (CI) tests to pass.
5. Make a new release through the GitHub interface. A CI job will automatically upload the packages to PyPI.
7. Optionally update the [Bioconda package](https://github.com/bioconda/bioconda-recipes/blob/master/recipes/bioblend/meta.yaml).

How to run BioBlend tests
-------------------------

1.  Clone galaxy in ~ via `git clone https://github.com/galaxyproject/galaxy.git`
2.  Copy sample galaxy config file via `cp ~/galaxy/config/galaxy.yml.sample ~/galaxy/config/galaxy.yml`
3.  Open ~/galaxy/config/galaxy.yml in an editor, uncomment `master_api_key` line, set it to a value, and save your change
4.  Start galaxy by running `~/galaxy/run.sh`
5.  In a browser, type `127.0.0.1:8080` and login to galaxy by clicking on `Login or Register`
6.  Select User -> Preferences -> Manage API Key. Create a new API key and save the key value
7.  Clone bioblend in ~ via `git clone https://github.com/galaxyproject/bioblend`
8.  Set the following environment variables by running these commands in a terminal. Use master API key in step 3, your login email in step 6, and API key in step 7. Change galaxy version and job timeout, if needed

    *  `export BIOBLEND_GALAXY_API_KEY=<ApiKey>`

    *  `export BIOBLEND_GALAXY_MASTER_API_KEY=<MasterApiKey>`

    *  `export BIOBLEND_GALAXY_URL=http://127.0.01:8080`

    *  `export BIOBLEND_GALAXY_USER_EMAIL=<YourLoginEmail>`

    *  `export BIOBLEND_TEST_JOB_TIMEOUT=100`

    *  `export GALAXY_VERSION=21.09`

9.  Run bioblend tests via `~/bioblend/run_bioblend_tests.sh -g ~/galaxy -e py39 2>&1 | tee log.txt`

    *  Pass your machine's Python version via `-e` flag. E.g., pass `py39` for Python 3.9

    *  Re-route stderr to stdout via `2>&1` and `tee` the output so you can both view it and save it to log.txt
