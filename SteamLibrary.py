#! /usr/bin/env python3
'''
SteamLibrary (Niema Moshiri 2021)
'''

# useful constants
WINDOW_TITLE = "SteamLibrary - Niema Moshiri"
STEAM_COMMUNITY_BASE_URL = "https://steamcommunity.com/id"
ERROR_IMPORT_PROMPT_TOOLKIT = "Unable to import 'prompt_toolkit'. Install via: 'pip install prompt_toolkit'"

# built-in imports
from sys import stderr

# error message
def error(s):
    print("ERROR: %s" % s, file=stderr); exit(1)

# non-built-in imports
try:
    from prompt_toolkit.shortcuts import message_dialog
except:
    error(ERROR_IMPORT_PROMPT_TOOLKIT)

# apps
APPS = {
    'welcome': message_dialog(title=WINDOW_TITLE, text="hola"),
}

# main content
if __name__ == "__main__":
    # show welcome message
    APPS['welcome'].run()
