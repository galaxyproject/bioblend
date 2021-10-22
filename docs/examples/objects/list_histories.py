"""
This example retrieves details of all the Histories in our Galaxy account and lists information on them.

Usage: python list_histories.py <Galaxy_URL> <Galaxy_API_key>
"""

import sys

from bioblend.galaxy.objects import GalaxyInstance

if len(sys.argv) != 3:
    print("Usage: python list_histories.py <Galaxy_URL> <Galaxy_API_key>")
    sys.exit(1)
galaxy_url = sys.argv[1]
galaxy_key = sys.argv[2]

print("Initiating Galaxy connection")

gi = GalaxyInstance(galaxy_url, galaxy_key)

print("Retrieving History list")

# histories.get_previews() returns a list of HistoryPreview objects, which contain only basic information
# histories.list() method returns a list of History objects, which contain more extended information
# As an example, we will use a piece of metadata (the size) from the 'wrapped' data attribute of History
histories = gi.histories.list()

if len(histories) == 0:
    print("There are no Histories in your account.")
else:
    print("\nHistories:")
    for hist in histories:
        print(f"{hist.name} ({hist.wrapped['nice_size']}) : {hist.id}")
