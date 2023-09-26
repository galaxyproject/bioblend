"""
Cookie handler for Authelia authentication using the Galaxy API
"""

import getpass
import sys
from http.cookiejar import LWPCookieJar
from pathlib import Path
from pprint import pprint

import requests
from galaxy_api import get_inputs, get_workflows

AUTH_HOSTNAME = "auth.service.org"
API_HOSTNAME = "galaxy.service.org"
cookie_path = Path(".galaxy_auth.txt")
cookie_jar = LWPCookieJar(cookie_path)


class ExpiredCookies(Exception):
    pass


class NoCookies(Exception):
    pass


def main():
    try:
        cookie_jar.load()  # raises OSError
        if not cookie_jar:  # if empty due to expirations
            raise ExpiredCookies()
    except OSError:
        print("No cached session found, please authenticate")
        prompt_authentication()
    except ExpiredCookies:
        print("Session has expired, please authenticate")
        prompt_authentication()
    run_examples()


def prompt_authentication():
    # --------------------------------------------------------------------------
    # Prompt for username and password

    username = input("Please enter username: ")
    password = getpass.getpass(f"Please enter password for {username}: ")

    # --------------------------------------------------------------------------
    # Prepare authentication packet and authenticate session using Authelia

    login_body = {
        "username": username,
        "password": password,
        "requestMethod": "GET",
        "keepMeLoggedIn": True,
        "targetURL": API_HOSTNAME,
    }

    with requests.Session() as session:
        session.cookies = cookie_jar
        session.verify = True

        session.post(f"https://{AUTH_HOSTNAME}/api/firstfactor", json=login_body)

        response = session.get(f"https://{AUTH_HOSTNAME}/api/user/info")
        if response.status_code != 200:
            print("Authentication failed")
            sys.exit()
        else:
            pprint(response.json())
            session.cookies.save()


def run_examples():
    GALAXY_KEY = "user_api_key"
    WORKFLOW_NAME = "workflow_name"
    with requests.Session() as session:
        session.cookies = cookie_jar

        print("Running demo to demonstrate how to use the Galaxy API with Authelia")

        print("Getting workflows from Galaxy")
        response = get_workflows(f"https://{API_HOSTNAME}", GALAXY_KEY, session=session)
        print(response)

        print("Getting inputs for a workflow")
        response = get_inputs(f"https://{API_HOSTNAME}", GALAXY_KEY, WORKFLOW_NAME, session=session)
        print(response)


if __name__ == "__main__":
    main()
