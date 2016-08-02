"""
This example retrieves details of all the Workflows in our Galaxy account and lists information on them.

Usage: python list_workflows.py <Galaxy_URL> <Galaxy_API_key>
"""
from __future__ import print_function

import sys

from bioblend.galaxy.objects import GalaxyInstance

if len(sys.argv) != 3:
    print("Usage: python list_workflows.py <Galaxy_URL> <Galaxy_API_key>")
    sys.exit(1)
galaxy_url = sys.argv[1]
galaxy_key = sys.argv[2]

print("Initiating Galaxy connection")

gi = GalaxyInstance(galaxy_url, galaxy_key)

print("Retrieving Workflows list")

workflows = gi.workflows.get_previews()

if len(workflows) == 0:
    print("There are no Workflows in your account.")
else:
    print("\nWorkflows:")
    for wf in workflows:
        print("{0} : {1}".format(wf.name, wf.id))
