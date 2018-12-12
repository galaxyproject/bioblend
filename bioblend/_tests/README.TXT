To run the cloud tests, the following environment variables must be set:

BIOBLEND_ACCESS_KEY = <your cloud access key>
BIOBLEND_SECRET_KEY = <your cloud secret key>
BIOBLEND_CLOUD_TYPE = <cloud type: EC2, NECTAR etc.>
BIOBLEND_AMI_ID =  <machine image id for cloudman>


To run Galaxy tests, the following environment variables must be set:

BIOBLEND_GALAXY_API_KEY = <web API key of a running galaxy instance>
BIOBLEND_GALAXY_URL = <root url for a running galaxy instance like http://localhost:8080>

If you wish to run the entire suite, set all of the above.  The integration
tests can subsequently be run by invoking `pytest` from the command line.
pytest should be invoked from the project root folder, and not the tests
child folder, since the test data is resolved relative to the bioblend folder.
