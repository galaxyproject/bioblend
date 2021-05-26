"""
This example retrieves details of all the Data Libraries available to us and lists information on them.

Usage: python3 list_data_libraries.py <galaxy-url> <galaxy-API-key>
"""

import sys

from bioblend.galaxy import GalaxyInstance

if len(sys.argv) != 3:
    print("Usage: python3 list_data_libraries.py <galaxy-url> <galaxy-API-key>")
    sys.exit(1)
galaxy_url = sys.argv[1]
galaxy_key = sys.argv[2]

print("Initiating Galaxy connection")

gi = GalaxyInstance(url=galaxy_url, key=galaxy_key)

print("Retrieving Data Library list")

libraries = gi.libraries.get_libraries()

if len(libraries) == 0:
    print("There are no Data Libraries available.")
else:
    print("\nData Libraries:")
    for lib_dict in libraries:
        print(f"{lib_dict['name']} : {lib_dict['id']}")
