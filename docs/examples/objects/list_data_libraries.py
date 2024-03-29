"""
This example retrieves details of all the Data Libraries available to us and lists information on them.

Usage: python list_data_libraries.py <Galaxy_URL> <Galaxy_API_key>
"""

import sys

from bioblend.galaxy.objects import GalaxyInstance

if len(sys.argv) != 3:
    print("Usage: python list_data_libraries.py <Galaxy_URL> <Galaxy_API_key>")
    sys.exit(1)
galaxy_url = sys.argv[1]
galaxy_key = sys.argv[2]

print("Initiating Galaxy connection")

gi = GalaxyInstance(galaxy_url, api_key=galaxy_key)

print("Retrieving Data Library list")

libraries = gi.libraries.get_previews()

if len(libraries) == 0:
    print("There are no Data Libraries available.")
else:
    print("\nData Libraries:")
    for lib in libraries:
        print(f"{lib.name} : {lib.id}")
