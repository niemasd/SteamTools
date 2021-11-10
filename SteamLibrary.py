#! /usr/bin/env python3
'''
SteamLibrary (Niema Moshiri 2021)
'''

# useful constants
WINDOW_TITLE = "SteamLibrary - Niema Moshiri"
STEAM_COMMUNITY_BASE_URL = "https://steamcommunity.com/id"
STEAM_COMMUNITY_BASE_URL_SUFFIX = "games?xml=1"
STEAM_APP_DETAILS_BASE_URL = "https://store.steampowered.com/api/appdetails?appids="
TEXT_LOADING_USER_DATA = "Loading user data"
TEXT_USER_PROMPT = "Please enter your Steam username:"
TEXT_WELCOME = "Welcome to SteamLibrary! This simple tool aims to provide a user-friendly command-line interface for navigating your Steam library."
ERROR_IMPORT_PROMPT_TOOLKIT = "Unable to import 'prompt_toolkit'. Install via: 'pip install prompt_toolkit'"
ERROR_INVALID_GAME = "Invalid game"
ERROR_LOAD_GAMES_FAILED = "Failed to load game library"

# built-in imports
from json import loads as jloads
from sys import stderr, stdout
from urllib.request import urlopen
from xml.etree import ElementTree

# message
def message(s='', end='\n'):
    print(s, end=end); stdout.flush()

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
        data = dict()
        for item in game:
            data[item.tag] = item.text
        if 'name' not in data or 'appID' not in data:
            error_app("%s: %s" % (ERROR_INVALID_GAME, str(game)))
        self.name = data['name']
        self.appID = data['appID']

    # view game app
    def view_app(self):
        try:
            details = jloads(urlopen("%s%s" % (STEAM_APP_DETAILS_BASE_URL, self.appID)).read().decode())[self.appID]['data']
        except:
            details = dict()
        text = ''
        #text += '<ansired>- Name: </ansired> %s\n' % self.name
        text += '<ansired>- App ID:</ansired> %s\n' % self.appID
        if 'release_date' in details and 'date' in details['release_date']:
            text += '<ansired>- Release Date:</ansired> %s\n' % details['release_date']['date']
        if 'developers' in details:
            text += '<ansired>- Developers:</ansired> %s\n' % ', '.join(details['developers'])
        if 'publishers' in details:
            text += '<ansired>- Publishers:</ansired> %s\n' % ', '.join(details['publishers'])
        if 'price_overview' in details and 'final_formatted' in details['price_overview']:
            text += '<ansired>- Price:</ansired> %s\n' % details['price_overview']['final_formatted']
        if 'achievements' in details and 'total' in details['achievements']:
            text += '<ansired>- Achievements:</ansired> %s\n' % details['achievements']['total']
        if 'genres' in details:
            text += '<ansired>- Genres:</ansired> %s\n' % ', '.join(sorted(g['description'] for g in details['genres']))
        if 'categories' in details:
            text += '<ansired>- Categories:</ansired> %s\n' % ', '.join(sorted(c['description'] for c in details['categories']))
        #if 'controller_support' in details:
        #    text += '<ansired>- Controller Support:</ansired> %s\n' % details['controller_support']
        if 'supported_languages' in details:
            text += '<ansired>- Supported Languages:</ansired> %s\n' % details['supported_languages'].replace('<strong>','').replace('</strong>','').replace('<br>','; ')
        #if 'short_description' in details:
        #    text += '<ansired>- Description:</ansired> %s\n' % details['short_description']
        message_dialog(title=self.name, text=HTML(text)).run()

    # str function
    def __str__(self):
        return str(self.__dict__)

    # comparison functions
    def __lt__(self, o):
        return self.name.lower() < o.name.lower()
    def __le__(self, o):
        return self.name.lower() <= o.name.lower()
    def __gt__(self, o):
        return self.name.lower() > o.name.lower()
    def __ge__(self, o):
        return self.name.lower() >= o.name.lower()
    def __eq__(self, o):
        return self.appID == o.appID

# main content
if __name__ == "__main__":
    # show welcome message and prompt user for Steam username
    APPS['welcome'].run(); username = APPS['user_prompt'].run()
    if username is None or username == '':
        exit(1)

    # load user data
    message(s="%s: %s" % (TEXT_LOADING_USER_DATA, username))
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

    # load game data
    games_list = sorted(Game(xml_game) for xml_game in xml_games)
    games_map = {game.appID:game for game in games_list}

    # view games (might need to move this into its own function if I want to add a filtering option)
    game_list_dialog = radiolist_dialog(title=WINDOW_TITLE, text="HELLO", values=[(game,game.name) for game in games_list])
    while True:
        game_selection = game_list_dialog.run()
        if game_selection is None:
            break
        game_selection.view_app()
