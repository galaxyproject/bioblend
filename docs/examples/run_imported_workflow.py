"""
This example demonstrates running a tophat+cufflinks workflow over paired-end data.
This is a task we could not do using Galaxy's GUI batch mode, because the inputs need to be paired.
The workflow is imported from a json file (previously exported from Galaxy), and the input data files from URLs.

This example creates a new Data Library, so you must be a Galaxy Admin on the instance you run the script against.

Also note that a Galaxy Workflow will only run without modification if it finds the expected versions of tool wrappers
installed on the Galaxy instance. This is to ensure reproducibility.
In this case we expect Tophat wrapper 1.5.0 and Cufflinks wrapper 0.0.5.

Usage: python3 run_imported_workflow.py <galaxy-url> <galaxy-API-key>
"""

import sys

from bioblend import galaxy

# Specify workflow and data to import into Galaxy

workflow_file = 'tophat_cufflinks_pairedend_workflow.ga'

import_file_pairs = [
    ('https://bioblend.s3.amazonaws.com/C1_R1_1.chr4.fq', 'https://bioblend.s3.amazonaws.com/C1_R1_2.chr4.fq'),
    ('https://bioblend.s3.amazonaws.com/C1_R2_1.chr4.fq', 'https://bioblend.s3.amazonaws.com/C1_R2_2.chr4.fq'),
    ('https://bioblend.s3.amazonaws.com/C1_R3_1.chr4.fq', 'https://bioblend.s3.amazonaws.com/C1_R3_2.chr4.fq')
]

# Specify names of Library and History that will be created in Galaxy
# In this simple example, these will be created even if items with the same name already exist.

library_name = 'Imported data for API demo'
output_history_name = 'Output from API demo'

if len(sys.argv) != 3:
    print("Usage: python3 run_imported_workflow.py <galaxy-url> <galaxy-API-key>")
    sys.exit(1)
galaxy_url = sys.argv[1]
galaxy_key = sys.argv[2]

print("Initiating Galaxy connection")

gi = galaxy.GalaxyInstance(url=galaxy_url, key=galaxy_key)

print("Importing workflow")

wf_import_dict = gi.workflows.import_workflow_from_local_path(workflow_file)
workflow = wf_import_dict['id']

print(f"Creating data library '{library_name}'")

library_dict = gi.libraries.create_library(library_name)
library = library_dict['id']

print("Importing data")

# Import each pair of files, and track the resulting identifiers.

dataset_ids = []
filenames = {}
for (file1, file2) in import_file_pairs:
    dataset1 = gi.libraries.upload_file_from_url(library, file1, file_type='fastqsanger')
    dataset2 = gi.libraries.upload_file_from_url(library, file2, file_type='fastqsanger')
    id1, id2 = dataset1[0]['id'], dataset2[0]['id']
    filenames[id1] = file1
    filenames[id2] = file2
    dataset_ids.append((id1, id2))

print(f"Creating output history '{output_history_name}'")

outputhist_dict = gi.histories.create_history(output_history_name)
outputhist = outputhist_dict['id']

print(f"Will run workflow on {len(dataset_ids)} pairs of files")

# Get the input step IDs from the workflow.
# We use the BioBlend convenience function get_workflow_inputs to retrieve inputs by label.

input1 = gi.workflows.get_workflow_inputs(workflow, label='Input fastq readpair-1')[0]
input2 = gi.workflows.get_workflow_inputs(workflow, label='Input fastq readpair-2')[0]

# For each pair of datasets we imported, run the imported workflow
# For each input we need to build a datamap dict with 'src' set to 'ld', as we stored our data in a Galaxy Library

for (data1, data2) in dataset_ids:
    print(f"Initiating workflow run on files {filenames[data1]}, {filenames[data2]}")
    datamap = {
        input1: {'src': 'ld', 'id': data1},
        input2: {'src': 'ld', 'id': data2},
    }
    result = gi.workflows.run_workflow(workflow, datamap, history_id=outputhist, import_inputs_to_history=True)
