import sys, os
from bioblend.galaxy.objects import GalaxyInstance
from common import get_one

URL = 'http://orione.crs4.it'
API_KEY = os.getenv('GALAXY_API_KEY', 'YOUR_API_KEY')
if API_KEY == 'YOUR_API_KEY':
    sys.exit('API_KEY not set, see the README.txt file')
gi = GalaxyInstance(URL, API_KEY)

# Select "W5 - Metagenomics" from published workflows

workflow_name = 'W5 - Metagenomics'
previews = gi.workflows.get_previews(name=workflow_name, published=True)
p = get_one(_ for _ in previews if _.published)

# Import the workflow to user space

iw = gi.workflows.import_shared(p.id)

# Select the "Orione SupMat" library

library_name = 'Orione SupMat'
l = get_one(gi.libraries.list(name=library_name))

# Select the "/Metagenomics/MetagenomicsDataset.fq" dataset

ds_name = '/Metagenomics/MetagenomicsDataset.fq'
ld = get_one(l.get_datasets(name=ds_name))
input_map = {'Input Dataset': ld}

# Select the blastn step

ws = get_one(_ for _ in iw.info.steps.itervalues()
             if _['tool_id'] and 'blastn' in _['tool_id'])
tool_id = ws['tool_id']

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
