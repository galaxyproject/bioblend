"""
This example creates a new user and prints her API key. It is also used to
initialize a Galaxy server in Continuous Integration testing of BioBlend.

Usage: python3 create_user_get_api_key.py <Galaxy_URL> <Galaxy_API_key> <new_username> <new_user_email> <new_password>
"""

import sys

import bioblend.galaxy

if len(sys.argv) != 6:
    print("Usage: python3 create_user_get_api_key.py <Galaxy_URL> <Galaxy_API_key> <new_username> <new_user_email> <new_password>")
    sys.exit(1)
galaxy_url = sys.argv[1]
galaxy_api_key = sys.argv[2]

# Initiating Galaxy connection
gi = bioblend.galaxy.GalaxyInstance(galaxy_url, galaxy_api_key)

# Create a new user and get a new API key for her
new_user = gi.users.create_local_user(sys.argv[3], sys.argv[4], sys.argv[5])
new_api_key = gi.users.create_user_apikey(new_user['id'])
print(new_api_key)
