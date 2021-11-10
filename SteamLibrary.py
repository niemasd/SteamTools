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
ERROR_INVALID_GAME = "Invalid game"
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
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.shortcuts import input_dialog, message_dialog, radiolist_dialog
except:
    error(ERROR_IMPORT_PROMPT_TOOLKIT)

# apps
APPS = {
    'welcome': message_dialog(title=WINDOW_TITLE, text=TEXT_WELCOME),
    'user_prompt': input_dialog(title=WINDOW_TITLE, text=TEXT_USER_PROMPT)
}

# helper class to represent individual games
class Game:
    # constructor
    def __init__(self, game):
        self.data = dict()
        for item in game:
            self.data[item.tag] = item.text
        if 'name' not in self.data:
            error_app("%s: %s" % (ERROR_INVALID_GAME, str(game)))

    # view game app
    def view_app(self):
        message_dialog(title=self.data['name'], text=HTML('\n'.join('<ansired>- %s:</ansired> %s' % (k,v) for k,v in self.data.items()))).run()

    # str function
    def __str__(self):
        return str(self.data)

    # comparison functions
    def __lt__(self, o):
        return self.data['name'].lower() < o.data['name'].lower()
    def __le__(self, o):
        return self.data['name'].lower() <= o.data['name'].lower()
    def __gt__(self, o):
        return self.data['name'].lower() > o.data['name'].lower()
    def __ge__(self, o):
        return self.data['name'].lower() >= o.data['name'].lower()
    def __eq__(self, o):
        return self.data == o.data

# main content
if __name__ == "__main__":
    # show welcome message and prompt user for Steam username
    APPS['welcome'].run(); username = APPS['user_prompt'].run()
    if username is None or username == '':
        exit(1)

    # load user data
    url = "%s/%s/%s" % (STEAM_COMMUNITY_BASE_URL, username, STEAM_COMMUNITY_BASE_URL_SUFFIX)
    xml = ElementTree.parse(urlopen(url)); xml_games = None
    try:
        for curr in xml.getroot():
            if curr.tag == 'games':
                xml_games = curr; break
    except:
        pass
    if xml_games is None:
        error_app(ERROR_LOAD_GAMES_FAILED)
    games_list = sorted(Game(xml_game) for xml_game in xml_games)

    # view games
    game_list_dialog = radiolist_dialog(title=WINDOW_TITLE, text="HELLO", values=[(game,game.data['name']) for game in games_list])
    while True:
        game_selection = game_list_dialog.run()
        if game_selection is None:
            break
        game_selection.view_app()
