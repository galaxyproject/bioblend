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

from bioblend.galaxy.objects import *

gi = GalaxyInstance(URL, API_KEY)

# Select workflows by name and restrict to published workflows
workflow_name = 'W5 - Metagenomics'
workflows = gi.workflows.list(name=workflow_name, published=True)
w = [workflow for workflow in workflows if workflow.published]
if len(w) != 1:
    raise Exception, 'Wrong number of published workflows found for name "%s"' % workflow_name
w = w[0]

# Import the selected published workflow
iw = gi.workflows.import_shared(w.id)

# Select a data library by name
library_name = 'Orione SupMat'
l = gi.libraries.list(library_name)
if len(l) != 1:
    raise Exception, 'Wrong number of libraries found for name "%s"' % library_name
l = l[0]

# Get the contents of the selected library and select a dataset by name
#TODO

# Select a workflow step by tool id
tool_id = 'ncbi_blastn_wrapper'
ws = [step for step in iw.tools if step.tool_id == tool_id]
if len(ws) != 1:
    raise Exception, 'Wrong number of workflow steps found for tool id "%s"' % tool_id
ws = ws[0]

# Get (a copy of) the tool parameters for the selected workflow step
ws_parameters = ws.tool_state.copy()

# Run the imported workflow on a new history with the selected dataset
# as input and modifying a tool parameter for the selected workflow step
history_name = workflow_name
params = {tool_id: {'db_opts': ws_parameters['db_opts']}}
params[tool_id]['db_opts']['database'] = '16SMicrobial-20131106'
inputs = [] #TODO
iw.run(inputs, history_name, params=params)
