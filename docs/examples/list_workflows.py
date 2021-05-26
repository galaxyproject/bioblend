"""
This example retrieves details of all the Workflows in our Galaxy account and lists information on them.

Usage: python list_workflows.py <galaxy-url> <galaxy-API-key>
"""

import sys

from bioblend.galaxy import GalaxyInstance

if len(sys.argv) != 3:
    print("Usage: python list_workflows.py <galaxy-url> <galaxy-API-key>")
    sys.exit(1)
galaxy_url = sys.argv[1]
galaxy_key = sys.argv[2]

print("Initiating Galaxy connection")

gi = GalaxyInstance(url=galaxy_url, key=galaxy_key)

print("Retrieving Workflows list")

workflows = gi.workflows.get_workflows()

if len(workflows) == 0:
    print("There are no Workflows in your account.")
else:
    print("\nWorkflows:")
    for wf_dict in workflows:
        print(f"{wf_dict['name']} : {wf_dict['id']}")
