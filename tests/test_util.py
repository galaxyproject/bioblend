""" General support infrastructure not tied to any particular test.
"""
import os
import unittest

NO_CLOUDMAN_MESSAGE = "CloudMan required and no CloudMan AMI configured."
NO_GALAXY_MESSAGE = "Externally configured Galaxy required, but not found. Set BIOBLEND_GALAXY_URL and BIOBLEND_GALAXY_API_KEY to run this test."


def skip_unless_cloudman():
    """ Decorate tests with this to skip the test if CloudMan is not
    configured.
    """
    test = lambda f: f
    if 'BIOBLEND_AMI_ID' not in os.environ:
        test = unittest.skip(NO_CLOUDMAN_MESSAGE)
    return test


def skip_unless_galaxy():
    """ Decorate tests with this to skip the test if Galaxy is not
    configured.
    """
    test = lambda f: f
    for prop in ['BIOBLEND_GALAXY_URL', 'BIOBLEND_GALAXY_API_KEY']:
        if prop not in os.environ:
            test = unittest.skip(NO_GALAXY_MESSAGE)
            break

    return test
