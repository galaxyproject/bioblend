from bioblend.galaxy.objects import GalaxyInstance

# This example uses a workflow and datasets publicly available on
# CRS4's Orione Galaxy server.

URL = 'http://orione.crs4.it'

# To use the Galaxy API you need an API key. To get one, proceed as follows:
#   1) go to http://orione.crs4.it and register, or log in if you are
#      already registered, through the "User" menu on the top;
#   2) open "User" -> "API Keys";
#   3) generate your API key if you don't have one;
#   4) in the following code, replace YOUR_API_KEY with your API key.

API_KEY = 'YOUR_API_KEY'
gi = GalaxyInstance(URL, API_KEY)

# Select "W5 - Metagenomics" from published workflows

workflow_name = 'W5 - Metagenomics'
previews = gi.workflows.get_previews(name=workflow_name, published=True)
p = [_ for _ in previews if _.published]
assert len(p) == 1
p = p[0]

# Import the workflow to user space

iw = gi.workflows.import_shared(p.id)

# Select the "Orione SupMat" library

library_name = 'Orione SupMat'
l = gi.libraries.list(name=library_name)
assert len(l) == 1
l = l[0]

# Select the "/Metagenomics/MetagenomicsDataset.fq" dataset

ds_name = '/Metagenomics/MetagenomicsDataset.fq'
ld = l.get_datasets(name=ds_name)
assert len(ld) == 1
input_map = {'Input Dataset': ld[0]}

# Select the "ncbi_blastn_wrapper" step

tool_id = 'ncbi_blastn_wrapper'
ws = [_ for _ in iw.info.steps.itervalues() if _['tool_id'] == tool_id]
assert len(ws) == 1
ws = ws[0]

# Get (a copy of) the parameters dict for the selected step

ws_parameters = ws['tool_inputs'].copy()

# Run the workflow on a new history with the selected dataset
# as input, setting the BLAST db to "16SMicrobial-20131106"

history_name = '%s output' % workflow_name
params = {tool_id: {'db_opts': ws_parameters['db_opts']}}
params[tool_id]['db_opts']['database'] = '16SMicrobial-20131106'
outputs, out_hist = iw.run(input_map, history_name, params=params)
assert out_hist.name == history_name

print 'Running workflow: %s [%s]' % (iw.name, iw.id)
print 'Output history: %s [%s]' % (out_hist.name, out_hist.id)
