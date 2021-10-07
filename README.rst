.. image:: https://img.shields.io/pypi/v/bioblend.svg
    :target: https://pypi.org/project/bioblend/
    :alt: latest version available on PyPI

.. image:: https://readthedocs.org/projects/bioblend/badge/
    :alt: Documentation Status
    :target: https://bioblend.readthedocs.io/

.. image:: https://badges.gitter.im/galaxyproject/bioblend.svg
   :alt: Join the chat at https://gitter.im/galaxyproject/bioblend
   :target: https://gitter.im/galaxyproject/bioblend?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge


BioBlend is a Python library for interacting with `Galaxy`_ and  `CloudMan`_
APIs.

BioBlend is supported and tested on:

- Python 3.6, 3.7, 3.8, 3.9 and 3.10
- Galaxy release_17.09 and later.

Full docs are available at https://bioblend.readthedocs.io/ with a quick library
overview also available in `ABOUT.rst <./ABOUT.rst>`_.

.. References/hyperlinks used above
.. _CloudMan: https://galaxyproject.org/cloudman/
.. _Galaxy: https://galaxyproject.org/

How to run BioBlend tests
*************************

1.  Clone galaxy in ~ via `git clone https://github.com/galaxyproject/galaxy.git`
2.  Copy sample galaxy config file via `cp ~/galaxy/config/galaxy.yml.sample ~/galaxy/config/galaxy.yml`
3.  Open ~/galaxy/config/galaxy.yml in an editor, uncomment `master_api_key` line, set it to a value, and save your change
4.  Start galaxy by running `~/galaxy/run.sh`
5.  In a browser, type `127.0.0.1:8080` and login to galaxy by clicking on `Login or Register
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
