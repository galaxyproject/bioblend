from __future__ import print_function
import os
import sys

from bioblend.galaxy.objects import GalaxyInstance
from common import get_one

URL = 'https://orione.crs4.it'
API_KEY = os.getenv('GALAXY_API_KEY', 'YOUR_API_KEY')
if API_KEY == 'YOUR_API_KEY':
    sys.exit('API_KEY not set, see the README.txt file')
gi = GalaxyInstance(URL, API_KEY)

# Select "W3 - Bacterial de novo assembly | Paired-end" from published workflows

workflow_name = 'W3 - Bacterial de novo assembly | Paired-end'
previews = gi.workflows.get_previews(name=workflow_name, published=True)
p = get_one(_ for _ in previews if _.published)

# Import the workflow to user space

iw = gi.workflows.import_shared(p.id)

# Create a new history

history_name = '%s output' % workflow_name
h = gi.histories.create(history_name)

# Select the "Orione SupMat" library

library_name = 'Orione SupMat'
l = get_one(gi.libraries.list(name=library_name))

# Select the datasets

ds_names = [
    '/Whole genome - Escherichia coli/E coli DH10B MiSeq R1.fastq',
    '/Whole genome - Escherichia coli/E coli DH10B MiSeq R2.fastq',
]
input_labels = [
    'Left/Forward FASTQ Reads',
    'Right/Reverse FASTQ Reads',
]
input_map = dict((label, h.import_dataset(get_one(l.get_datasets(name=name))))
                 for name, label in zip(ds_names, input_labels))

# Set the "hash_length" parameter to different values for the 3 "velveth" steps

lengths = set(['19', '23', '29'])
ws_ids = iw.tool_labels_to_ids['velveth']
assert len(ws_ids) == len(lengths)
params = dict((id_, {'hash_length': v}) for id_, v in zip(ws_ids, lengths))

# Set the "ins_length" runtime parameter to the same value for the 3
# "velvetg" steps

tool_id = 'velvetg'
ws_ids = iw.tool_labels_to_ids[tool_id]
step = iw.steps[next(iter(ws_ids))]  # arbitrarily pick one
params[tool_id] = {'reads': step.tool_inputs['reads'].copy()}
params[tool_id]['reads']['ins_length'] = -1

# Set more custom parameters

params['cisarunner'] = {'genomesize': 5000000}
params['check_contigs'] = {'genomesize': 5.0}
params[
    'toolshed.g2.bx.psu.edu/repos/edward-kirton/abyss_toolsuite/abyss/1.0.0'
] = {'k': 41}

# Run the workflow on a new history with the selected datasets as inputs

outputs, out_hist = iw.run(input_map, h, params=params)
assert out_hist.name == history_name

print('Running workflow: %s [%s]' % (iw.name, iw.id))
print('Output history: %s [%s]' % (out_hist.name, out_hist.id))
