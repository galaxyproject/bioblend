import json
import os
import sys
from urllib.parse import urljoin

# This example, provided for comparison with w5_metagenomics.py,
# contains the code required to run the metagenomics workflow
# *without* BioBlend.

URL = os.getenv('GALAXY_URL', 'https://orione.crs4.it')
API_URL = urljoin(URL, 'api')
API_KEY = os.getenv('GALAXY_API_KEY', 'YOUR_API_KEY')
if API_KEY == 'YOUR_API_KEY':
    sys.exit('API_KEY not set, see the README.txt file')

# Clone the galaxy git repository and replace
# YOUR_GALAXY_PATH with the clone's local path in the following code, e.g.:
#   cd /tmp
#   git clone https://github.com/galaxyproject/galaxy
#   GALAXY_PATH = '/tmp/galaxy'

GALAXY_PATH = 'YOUR_GALAXY_PATH'
sys.path.insert(1, os.path.join(GALAXY_PATH, 'scripts/api'))
import common  # noqa: E402,I100,I202

# Select "W5 - Metagenomics" from published workflows

workflow_name = 'W5 - Metagenomics'
workflows = common.get(API_KEY, f"{API_URL}/workflows?show_published=True")
w = [_ for _ in workflows if _['published'] and _['name'] == workflow_name]
assert len(w) == 1
w = w[0]

# Import the workflow to user space

data = {'workflow_id': w['id']}
iw = common.post(API_KEY, f"{API_URL}/workflows/import", data)
iw_details = common.get(API_KEY, f"{API_URL}/workflows/{iw['id']}")

# Select the "Orione SupMat" library

library_name = 'Orione SupMat'
libraries = common.get(API_KEY, f"{API_URL}/libraries")
l = [_ for _ in libraries if _['name'] == library_name]
assert len(l) == 1
l = l[0]

# Select the "/Metagenomics/MetagenomicsDataset.fq" dataset

ds_name = '/Metagenomics/MetagenomicsDataset.fq'
contents = common.get(API_KEY, f"{API_URL}/libraries/{l['id']}/contents")
ld = [_ for _ in contents if _['type'] == 'file' and _['name'] == ds_name]
assert len(ld) == 1
ld = ld[0]

# Select the blastn step

ws = [_ for _ in iw_details['steps'].values()
      if _['tool_id'] and 'blastn' in _['tool_id']]
assert len(ws) == 1
ws = ws[0]
tool_id = ws['tool_id']

# Get (a copy of) the parameters dict for the selected step

ws_parameters = ws['tool_inputs'].copy()
for k, v in ws_parameters.items():
    ws_parameters[k] = json.loads(v)

# Run the workflow on a new history with the selected dataset
# as input, setting the BLAST db to "16SMicrobial-20131106"

history_name = f"{workflow_name} output"
ws_parameters['db_opts']['database'] = '16SMicrobial-20131106'
data = {
    'workflow_id': iw['id'],
    'parameters': {tool_id: {'db_opts': ws_parameters['db_opts']}},
}
assert len(iw_details['inputs']) == 1
input_step_id = iw_details['inputs'].keys()[0]
data['ds_map'] = {input_step_id: {'src': 'ld', 'id': ld['id']}}
data['history'] = history_name
r_dict = common.post(API_KEY, f"{API_URL}/workflows", data)

print(f"Running workflow: {iw['name']} [{iw['id']}]")
print(f"Output history: {history_name} [{r_dict['history']}]")
