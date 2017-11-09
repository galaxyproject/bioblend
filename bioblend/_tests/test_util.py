""" General support infrastructure not tied to any particular test.
"""
import os
import random
import string
import unittest

import bioblend

NO_CLOUDMAN_MESSAGE = "CloudMan required and no CloudMan AMI configured."
NO_GALAXY_MESSAGE = "Externally configured Galaxy required, but not found. Set BIOBLEND_GALAXY_URL and BIOBLEND_GALAXY_API_KEY to run this test."
OLD_GALAXY_RELEASE = "Testing on Galaxy %s, but need %s to run this test."
MISSING_TOOL_MESSAGE = "Externally configured Galaxy instance requires tool %s to run test."


def skip_unless_cloudman():
    """ Decorate tests with this to skip the test if CloudMan is not
    configured.
    """
    if 'BIOBLEND_AMI_ID' not in os.environ:
        return unittest.skip(NO_CLOUDMAN_MESSAGE)
    else:
        return lambda f: f


def skip_unless_galaxy(min_release=None):
    """ Decorate tests with this to skip the test if Galaxy is not
    configured.
    """
    if min_release is not None:
        galaxy_release = os.environ.get('GALAXY_VERSION', None)
        if galaxy_release is not None and galaxy_release != 'dev':
            if not galaxy_release.startswith('release_'):
                raise ValueError("The value of GALAXY_VERSION environment variable should start with 'release_'")
            if not min_release.startswith('release_'):
                raise Exception("min_release should start with 'release_'")
            if galaxy_release[8:] < min_release[8:]:
                return unittest.skip(OLD_GALAXY_RELEASE % (galaxy_release, min_release))

    if 'BIOBLEND_GALAXY_URL' not in os.environ:
        return unittest.skip(NO_GALAXY_MESSAGE)

    if 'BIOBLEND_GALAXY_API_KEY' not in os.environ and 'BIOBLEND_GALAXY_MASTER_API_KEY' in os.environ:
        galaxy_url = os.environ['BIOBLEND_GALAXY_URL']
        galaxy_master_api_key = os.environ['BIOBLEND_GALAXY_MASTER_API_KEY']
        gi = bioblend.galaxy.GalaxyInstance(galaxy_url, galaxy_master_api_key)

        if 'BIOBLEND_GALAXY_USER_EMAIL' in os.environ:
            galaxy_user_email = os.environ['BIOBLEND_GALAXY_USER_EMAIL']
        else:
            galaxy_user_email = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5)) + "@localhost.localdomain"

        galaxy_user_id = None
        for user in gi.users.get_users():
            if user["email"] == galaxy_user_email:
                galaxy_user_id = user["id"]
                break

        if galaxy_user_id is None:
            try:
                config = gi.config.get_config()
            except Exception:
                # If older Galaxy for instance just assume use_remote_user is False.
                config = {}

            if config.get("use_remote_user", False):
                new_user = gi.users.create_remote_user(galaxy_user_email)
            else:
                galaxy_user = galaxy_user_email.split("@", 1)[0]
                galaxy_password = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))

                # Create a new user and get a new API key for her
                new_user = gi.users.create_local_user(galaxy_user, galaxy_user_email, galaxy_password)
            galaxy_user_id = new_user["id"]

        api_key = gi.users.create_user_apikey(galaxy_user_id)
        os.environ["BIOBLEND_GALAXY_API_KEY"] = api_key

    if 'BIOBLEND_GALAXY_API_KEY' not in os.environ:
        return unittest.skip(NO_GALAXY_MESSAGE)

    return lambda f: f


def skip_unless_tool(tool_id):
    """ Decorate a Galaxy test method as requiring a specific tool,
    skip the test case if the tool is unavailable.
    """

    def method_wrapper(method):

        def wrapped_method(has_gi, *args, **kwargs):
            tools = has_gi.gi.tools.get_tools()
            # In panels by default, so flatten out sections...
            tool_ids = [_['id'] for _ in tools]
            if tool_id not in tool_ids:
                raise unittest.SkipTest(MISSING_TOOL_MESSAGE % tool_id)

            return method(has_gi, *args, **kwargs)

        # Must preserve method name so nose can detect and report tests by
        # name.
        wrapped_method.__name__ = method.__name__
        return wrapped_method

    return method_wrapper


def get_abspath(path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), path))
