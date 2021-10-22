"""
This example retrieves details of all the Histories in our Galaxy account and lists information on them.

Usage: python list_histories.py <galaxy-url> <galaxy-API-key>
"""

import sys

from bioblend.galaxy import GalaxyInstance

if len(sys.argv) != 3:
    print("Usage: python list_histories.py <galaxy-url> <galaxy-API-key>")
    sys.exit(1)
galaxy_url = sys.argv[1]
galaxy_key = sys.argv[2]

print("Initiating Galaxy connection")

gi = GalaxyInstance(url=galaxy_url, key=galaxy_key)

print("Retrieving History list")

histories = gi.histories.get_histories()

if len(histories) == 0:
    print("There are no Histories in your account.")
else:
    print("\nHistories:")
    for hist_dict in histories:
        # As an example, we retrieve a piece of metadata (the size) using show_history
        hist_details = gi.histories.show_history(hist_dict['id'])
        print(f"{hist_dict['name']} ({hist_details['size']}) : {hist_dict['id']}")
