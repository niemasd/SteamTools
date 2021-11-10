#! /usr/bin/env python3
'''
SteamLibrary (Niema Moshiri 2021)
'''

# useful constants
WINDOW_TITLE = "SteamLibrary - Niema Moshiri"
STEAM_COMMUNITY_BASE_URL = "https://steamcommunity.com/id"
STEAM_COMMUNITY_BASE_URL_SUFFIX = "games?xml=1"
TEXT_WELCOME = "Welcome to SteamLibrary! This simple tool aims to provide a user-friendly command-line interface for navigating your Steam library."
TEXT_USER_PROMPT = "Please enter your Steam username:"
ERROR_IMPORT_PROMPT_TOOLKIT = "Unable to import 'prompt_toolkit'. Install via: 'pip install prompt_toolkit'"
ERROR_LOAD_GAMES_FAILED = "Failed to load game library"

# built-in imports
from sys import stderr
from urllib.request import urlopen
from xml.etree import ElementTree

# error message
def error(s):
    print(s, file=stderr); exit(1)

# error message app
def error_app(s):
    message_dialog(title=WINDOW_TITLE, text="ERROR: %s" % s).run(); exit(1)

# non-built-in imports
try:
    from prompt_toolkit.shortcuts import input_dialog, message_dialog
except:
    error(ERROR_IMPORT_PROMPT_TOOLKIT)

# apps
APPS = {
    'welcome': message_dialog(title=WINDOW_TITLE, text=TEXT_WELCOME),
    'user_prompt': input_dialog(title=WINDOW_TITLE, text=TEXT_USER_PROMPT)
}

# main content
if __name__ == "__main__":
    # show welcome message and prompt user for Steam username
    APPS['welcome'].run()
    username = APPS['user_prompt'].run()

    # load user data
    url = "%s/%s/%s" % (STEAM_COMMUNITY_BASE_URL, username, STEAM_COMMUNITY_BASE_URL_SUFFIX)
    xml = ElementTree.parse(urlopen(url))
    xml_games = None
    try:
        for curr in xml.getroot():
            if curr.tag == 'games':
                xml_games = curr; break
    except:
        pass
    if xml_games is None:
        error_app(ERROR_LOAD_GAMES_FAILED)
    print(list(xml_games))
