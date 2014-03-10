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

# Select "W2 - Bacterial re-sequencing | Paired-end" from published workflows

workflow_name = 'W2 - Bacterial re-sequencing | Paired-end'
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
    '/Whole genome - Escherichia coli/E coli DH10B MiSeq R2.fastq',
    '/Whole genome - Escherichia coli/E coli DH10B MiSeq R1.fastq',
    '/Whole genome - Escherichia coli/E coli DH10B - Reference',
    ]
lds = []
for name in ds_names:
    ld = l.get_datasets(name=name)
    assert len(ld) == 1
    lds.extend(ld)

# Set custom parameters for the "check_contigs" and "sspace" tools

params = {
    'check_contigs': {'genomesize': 5.0},  # affects both occurrences
    'sspace': {'insert': 300, 'error': 0.5, 'minoverlap': 35},
    }

# Run the workflow on a new history with the selected datasets as inputs

history_name = '%s output' % workflow_name
outputs, out_hist = iw.run(lds, history_name, params=params)
assert out_hist.name == history_name

print 'Running workflow: %s [%s]' % (iw.name, iw.id)
print 'Output history: %s [%s]' % (out_hist.name, out_hist.id)
