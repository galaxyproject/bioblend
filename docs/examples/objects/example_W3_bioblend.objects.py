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

# Select "W3 - Bacterial de novo assembly | Paired-end" from published workflows

workflow_name = 'W3 - Bacterial de novo assembly | Paired-end'
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

# Select the datasets

ds_names = [
    '/Whole genome - Escherichia coli/E coli DH10B MiSeq R1.fastq',
    '/Whole genome - Escherichia coli/E coli DH10B MiSeq R2.fastq',
    ]
input_labels = [
    'Left/Forward FASTQ Reads',
    'Right/Reverse FASTQ Reads',
    ]
input_map = {}
for i in range(len(ds_names)):
    ld = l.get_datasets(name=ds_names[i])
    assert len(ld) == 1
    input_map[input_labels[i]] = ld[0]

# Set "hash_length" parameter to a different value for each of the 3 "velveth" steps

tool_id = 'velveth'
hash_length_values = ('19', '23', '29')
ws_ids = [k for k, v in iw.info.steps.iteritems() if v['tool_id'] == tool_id]
params = {}
assert len(ws_ids) == len(hash_length_values)
for i in range(len(ws_ids)):
    params[ws_ids[i]] = {'hash_length': hash_length_values[i]}

# Set "k" parameter for the "toolshed.g2.bx.psu.edu/repos/edward-kirton/abyss_toolsuite/abyss/1.0.0" step

params['toolshed.g2.bx.psu.edu/repos/edward-kirton/abyss_toolsuite/abyss/1.0.0'] = {'k': 41}

# Set "ins_length" parameter for the 3 "velvetg" steps

tool_id = 'velvetg'
ws = [_ for _ in iw.info.steps.itervalues() if _['tool_id'] == tool_id]
for i in range(len(ws)):
    ws_parameters = ws[i]['tool_inputs'].copy()
    params[ws[i]['id']] = {'reads': ws_parameters['reads']}
    params[ws[i]['id']]['reads']['ins_length'] = -1

# Set custom parameters for the "cisarunner" and "check_contigs" steps

params['cisarunner'] = {'genomesize': 5000000}
params['check_contigs'] = {'genomesize': 5.0}

# Run the workflow on a new history with the selected datasets as inputs

history_name = '%s output' % workflow_name
outputs, out_hist = iw.run(input_map, history_name, params=params)
assert out_hist.name == history_name

print 'Running workflow: %s [%s]' % (iw.name, iw.id)
print 'Output history: %s [%s]' % (out_hist.name, out_hist.id)
