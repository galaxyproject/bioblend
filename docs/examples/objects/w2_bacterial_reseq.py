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

# Select "W2 - Bacterial re-sequencing | Paired-end" from published workflows

workflow_name = 'W2 - Bacterial re-sequencing | Paired-end'
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
    '/Whole genome - Escherichia coli/E coli DH10B - Reference',
]
input_labels = [
    'Forward Reads',
    'Reverse Reads',
    'Reference Genome',
]
input_map = dict((label, h.import_dataset(get_one(l.get_datasets(name=name))))
                 for name, label in zip(ds_names, input_labels))

# Set custom parameters for the "check_contigs" and "sspace" tools

params = {
    'check_contigs': {'genomesize': 5.0},  # affects both occurrences
    'sspace': {'insert': 300, 'error': 0.5, 'minoverlap': 35},
}

# Run the workflow on a new history with the selected datasets as inputs

outputs, out_hist = iw.run(input_map, h, params=params)
assert out_hist.name == history_name

print('Running workflow: %s [%s]' % (iw.name, iw.id))
print('Output history: %s [%s]' % (out_hist.name, out_hist.id))
