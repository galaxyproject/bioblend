import json
import os
import sys

import requests

# This example, provided for comparison with w5_metagenomics.py,
# contains the code required to run the metagenomics workflow
# *without* BioBlend.

URL = os.getenv("GALAXY_URL", "https://orione.crs4.it").rstrip("/")
API_URL = f"{URL}/api"
API_KEY = os.getenv("GALAXY_API_KEY")
if not API_KEY:
    sys.exit("API_KEY not set, see the README.txt file")
headers = {"Content-Type": "application/json", "x-api-key": API_KEY}

# Select "W5 - Metagenomics" from published workflows

workflow_name = "W5 - Metagenomics"
r = requests.get(f"{API_URL}/workflows", params={"show_published": True}, headers=headers)
workflows = r.json()
filtered_workflows = [_ for _ in workflows if _["published"] and _["name"] == workflow_name]
assert len(filtered_workflows) == 1
w = filtered_workflows[0]

# Import the workflow to user space

data = {"workflow_id": w["id"]}
r = requests.post(f"{API_URL}/workflows/import", data=json.dumps(data), headers=headers)
iw = r.json()
r = requests.get(f"{API_URL}/workflows/{iw['id']}", headers=headers)
iw_details = r.json()

# Select the "Orione SupMat" library

library_name = "Orione SupMat"
r = requests.get(f"{API_URL}/libraries", headers=headers)
libraries = r.json()
filtered_libraries = [_ for _ in libraries if _["name"] == library_name]
assert len(filtered_libraries) == 1
library = filtered_libraries[0]

# Select the "/Metagenomics/MetagenomicsDataset.fq" dataset

ds_name = "/Metagenomics/MetagenomicsDataset.fq"
r = requests.get(f"{API_URL}/libraries/{library['id']}/contents", headers=headers)
contents = r.json()
filtered_contents = [_ for _ in contents if _["type"] == "file" and _["name"] == ds_name]
assert len(filtered_contents) == 1
ld = filtered_contents[0]

# Select the blastn step

filtered_wf_steps = [_ for _ in iw_details["steps"].values() if _["tool_id"] and "blastn" in _["tool_id"]]
assert len(filtered_wf_steps) == 1
ws = filtered_wf_steps[0]
tool_id = ws["tool_id"]

# Get (a copy of) the parameters dict for the selected step

ws_parameters = ws["tool_inputs"].copy()
for k, v in ws_parameters.items():
    ws_parameters[k] = json.loads(v)

# Run the workflow on a new history with the selected dataset
# as input, setting the BLAST db to "16SMicrobial-20131106"

history_name = f"{workflow_name} output"
ws_parameters["db_opts"]["database"] = "16SMicrobial-20131106"
data = {
    "workflow_id": iw["id"],
    "parameters": {tool_id: {"db_opts": ws_parameters["db_opts"]}},
}
assert len(iw_details["inputs"]) == 1
input_step_id = iw_details["inputs"].keys()[0]
data["ds_map"] = {input_step_id: {"src": "ld", "id": ld["id"]}}
data["history"] = history_name
r = requests.post(f"{API_URL}/workflows", data=json.dumps(data), headers=headers)
r_dict = r.json()

print(f"Running workflow: {iw['name']} [{iw['id']}]")
print(f"Output history: {history_name} [{r_dict['history']}]")
