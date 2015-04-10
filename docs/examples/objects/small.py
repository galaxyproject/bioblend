from __future__ import print_function
import os
import sys
import tempfile

from bioblend.galaxy.objects import GalaxyInstance
from common import get_one

# This is a "toy" example that should run much faster
# (once the cluster's resource manager allows it to run) than the
# real-world ones.  The workflow, which is imported from local disk,
# removes two header lines from a tabular file, then extracts one of
# the columns.  The input dataset is publicly available on CRS4's
# Orione Galaxy server.

URL = 'https://orione.crs4.it'
API_KEY = os.getenv('GALAXY_API_KEY', 'YOUR_API_KEY')
if API_KEY == 'YOUR_API_KEY':
    sys.exit('API_KEY not set, see the README.txt file')
gi = GalaxyInstance(URL, API_KEY)

# import the workflow from the JSON dump

with open("small.ga") as f:
    wf = gi.workflows.import_new(f.read())

# Select the "Orione SupMat" library

library_name = 'Orione SupMat'
l = get_one(gi.libraries.list(name=library_name))

# Select the input dataset

ds_name = '/RNA-Seq - Listeria monocytogenes/Listeria_monocytogenes_EGD_e_uid61583/NC_003210.rnt'
ld = get_one(l.get_datasets(name=ds_name))
input_map = {'input_tsv': ld}

# Run the workflow on a new history with the selected dataset as
# input, overriding the index of the column to remove; wait until the
# computation is complete.

history_name = 'get_col output'
params = {'Cut1': {'columnList': 'c2'}}
print('Running workflow: %s [%s]' % (wf.name, wf.id))
outputs, out_hist = wf.run(input_map, history_name, params=params, wait=True)
print('Job has finished')
assert out_hist.name == history_name
print('Output history: %s [%s]' % (out_hist.name, out_hist.id))

# Save results to local disk
out_ds = get_one([_ for _ in outputs if _.name == 'Cut on data 1'])
with tempfile.NamedTemporaryFile(prefix='bioblend_', delete=False) as f:
    out_ds.download(f)
print('Output downloaded to "%s"' % f.name)
