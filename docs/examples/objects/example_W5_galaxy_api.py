# This example will use a workflow and datasets publicly available on
# Orione Galaxy server.
URL = 'http://orione.crs4.it/'
# To use the Galaxy API you need an API key. Procedure:
# 1) go to http://orione.crs4.it/ and register, or login if you are
#    already registered, through the "User" menu on the top;
# 2) open "User" -> "API Keys";
# 3) generate your API key if you don't already have one;
# 4) replace YOUR_API_KEY with your API key on the line below.
API_KEY = 'YOUR_API_KEY'
# Make a local clone of https://bitbucket.org/galaxy/galaxy-dist/ and
# replace YOUR_GALAXY_PATH with its path on the line below
GALAXY_PATH = 'YOUR_GALAXY_PATH'

import json
import os.path
import sys
import urlparse

sys.path.insert(1, os.path.join(GALAXY_PATH, 'scripts/api'))
import common

# Get all published workflows and select a published workflow by name
workflows = common.get(API_KEY, urlparse.urljoin(URL, 'api/workflows?show_published=True'))
published_workflows = [workflow for workflow in workflows if workflow['published']]
workflow_name = 'W5 - Metagenomics'
w = [pw for pw in published_workflows if pw['name'] == workflow_name]
if len(w) != 1:
    raise Exception, 'Wrong number of workflows found for name "%s"' % workflow_name
w = w[0]

# Import the selected published workflow
# This is not needed if you are the owner of the workflow, an admin or
# if the workflow is shared with you. It would probably make sense to
# change the API to let a user run directly importable workflows too
data = {}
data['workflow_id'] = w['id']
iw = common.post(API_KEY, urlparse.urljoin(URL, 'api/workflows/import'), data)
iw_details = common.get(API_KEY, URL + 'api/workflows/' + iw['id'])

# Get all data libraries and select a library by name
libraries = common.get(API_KEY, urlparse.urljoin(URL, 'api/libraries'))
library_name = 'Orione SupMat'
l = [library for library in libraries if library['name'] == library_name]
if len(l) != 1:
    raise Exception, 'Wrong number of libraries found for name "%s"' % library_name
l = l[0]

# Get the contents of the selected library and select a dataset by name
l_contents = common.get(API_KEY, urlparse.urljoin(URL, 'api/libraries/' + l['id'] + '/contents'))
library_dataset_name = '/Metagenomics/MetagenomicsDataset.fq'
ld = [l_content for l_content in l_contents if l_content['type'] == 'file' and l_content['name'] == library_dataset_name]
if len(ld) != 1:
    raise Exception, 'Wrong number of library datasets found for name "%s"' % library_dataset_name
ld = ld[0]
ld_details = common.get(API_KEY, urlparse.urljoin(URL, 'api/libraries/' + l['id'] + '/contents/' + ld['id']))
ld_ldda_id = ld_details['ldda_id']

# Select a workflow step by tool id
tool_id = 'ncbi_blastn_wrapper'
ws = [step for step in iw_details['steps'].itervalues() if step['tool_id'] == tool_id]
if len(ws) != 1:
    raise Exception, 'Wrong number of workflow steps found for tool id "%s"' % tool_id
ws = ws[0]

# Get (a copy of) the tool parameters for the selected workflow step
ws_parameters = ws['tool_inputs'].copy()
for k, v in ws_parameters.iteritems():
    ws_parameters[k] = json.loads(v)

# Run the imported workflow on a new history with the selected dataset
# as input and modifying a tool parameter for the selected workflow step
history_name = workflow_name
data = {}
data['workflow_id'] = iw['id']
data['parameters'] = {tool_id: {'db_opts': ws_parameters['db_opts']}}
data['parameters'][tool_id]['db_opts']['database'] = '16SMicrobial-20131106'
iw_input_step_ids = iw_details['inputs'].keys()
data['ds_map'] = { iw_input_step_ids[0]: dict(src='ld', id=ld['id']) }
data['history'] = history_name
r_dict = common.post(API_KEY, urlparse.urljoin(URL, 'api/workflows'), data)

