To run the integration tests, the following environmental variables must be set:

BIOBLEND_ACCESS_KEY = <your cloud access key>
BIOBLEND_SECRET_KEY = <your cloud secret key>
BIOBLEND_CLOUD_TYPE = <cloud type: EC2, NECTAR etc.>
BIOBLEND_AMI_ID =  <machine image id for cloudman>
BIOBLEND_GALAXY_API_KEY = <web API key of a running galaxy instance>

The integration tests can subsequently be run by invoking
nosetests
from the command line. nosetests should be invoked from the bioblend folder, and not the tests folder,
since the test data is resolved relative to the bioblend folder.
