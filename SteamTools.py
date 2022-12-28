#! /usr/bin/env python3
'''
SteamTools (Niema Moshiri 2021)
'''

# useful constants
VERSION = '0.0.1'
WINDOW_TITLE = "SteamTools v%s" % VERSION
LINE_WIDTH = 120

# URL stuff
STEAM_COMMUNITY_BASE_URL = "https://steamcommunity.com/id"
STEAM_APP_DETAILS_BASE_URL = "https://store.steampowered.com/api/appdetails?appids="
STEAM_URL_SUFFIX_XML = "?xml=1"

# messages
TEXT_LOADING_USER_DATA = "Loading user data"
TEXT_USER_PROMPT = "Please enter your Steam username:"
TEXT_WELCOME = "Welcome to SteamTools! This simple tool aims to provide a user-friendly command-line interface for exploring a public Steam account.\n\nMade by Niema Moshiri (niemasd), 2021"
ERROR_IMPORT_PROMPT_TOOLKIT = "Unable to import 'prompt_toolkit'. Install via: 'pip install prompt_toolkit'"
ERROR_INVALID_GAME = "Invalid game"
ERROR_INVALID_GAMES_LIST_MODE = "Invalid games list mode"
ERROR_LOAD_GAMES_FAILED = "Failed to load game library"

# built-in imports
from json import loads as jloads
from sys import argv, stderr, stdout
from urllib.request import urlopen
from xml.etree import ElementTree

# message
def message(s='', end='\n'):
    print(s, end=end); stdout.flush()

# message app
def message_app(s):
    message_dialog(title=WINDOW_TITLE, text=s).run()

# error message
def error(s):
    print(s, file=stderr); exit(1)

# error message app
def error_app(s):
    message_dialog(title=WINDOW_TITLE, text="ERROR: %s" % s).run(); exit(1)

# break a long string into multiple lines
def break_string(s, max_width=LINE_WIDTH):
    col = 0; text = ''
    for word in s.split(' '):
        if col + len(word) + 1 >= max_width:
            text += '\n'; col = 0
        text += (word + ' '); col += (len(word) + 1)
    return text

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
        self.details = None

    # load game details
    def load_details(self):
        try:
            self.details = jloads(urlopen("%s%s" % (STEAM_APP_DETAILS_BASE_URL, self.appID)).read().decode())[self.appID]['data']
        except:
            self.details = dict()
        if 'supported_languages' in self.details:
            self.details['supported_languages'] = self.details['supported_languages'].replace('<strong>','').replace('</strong>','').replace('<br>',', ').split(', ')

    # view game details
    def view_details(self):
        if self.details is None:
            self.load_details()
        text = '<ansired>- App ID:</ansired> %s' % self.appID
        if 'release_date' in self.details and 'date' in self.details['release_date']:
            text += '\n<ansired>- Release Date:</ansired> %s' % self.details['release_date']['date']
        if 'developers' in self.details:
            text += '\n<ansired>- Developers:</ansired> %s' % ', '.join(self.details['developers'])
        if 'publishers' in self.details:
            text += '\n<ansired>- Publishers:</ansired> %s' % ', '.join(self.details['publishers'])
        if 'price_overview' in self.details and 'final_formatted' in self.details['price_overview']:
            text += '\n<ansired>- Price:</ansired> %s' % self.details['price_overview']['final_formatted']
        if 'achievements' in self.details and 'total' in self.details['achievements']:
            text += '\n<ansired>- Achievements:</ansired> %s' % self.details['achievements']['total']
        if 'genres' in self.details:
            text += '\n<ansired>- Genres:</ansired> %s' % break_string(', '.join(sorted(g['description'] for g in self.details['genres'])))
        if 'categories' in self.details:
            text += '\n<ansired>- Categories:</ansired> %s' % break_string(', '.join(c['description'] for c in self.details['categories']))
        if 'controller_support' in self.details:
            text += '\n<ansired>- Controller Support:</ansired> %s' % self.details['controller_support']
        if 'supported_languages' in self.details:
            text += '\n<ansired>- Supported Languages:</ansired> %s' % break_string(', '.join(self.details['supported_languages']))
        if 'short_description' in self.details:
            col = LINE_WIDTH
            text += '\n<ansired>- Short Description:</ansired>'
            text += break_string(self.details['short_description'])#.replace('\n', '\n    ')
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

# helper class to represent a user
class User:
    # constructor
    def __init__(self, username):
        # prepare for loading user data
        message(s="%s: %s" % (TEXT_LOADING_USER_DATA, username))
        self.username = username
        self.url_community = "%s/%s" % (STEAM_COMMUNITY_BASE_URL, self.username)
        self.url_games = "%s/games" % self.url_community

        # load user data
        xml = ElementTree.parse(urlopen(self.url_community + STEAM_URL_SUFFIX_XML))
        for curr in xml.getroot():
            try:
                if curr.tag == 'steamID64':
                    self.steamID64 = curr.text.strip()
                elif curr.tag == 'stateMessage':
                    self.online_state = curr.text.strip()
                elif curr.tag == 'avatarFull':
                    self.url_avatar = curr.text.strip()
                elif curr.tag == 'memberSince':
                    self.member_since = curr.text.strip()
                elif curr.tag == 'location':
                    self.location = curr.text.strip()
                elif curr.tag == 'realname':
                    self.real_name = curr.text.strip()
            except:
                pass

        # load game data
        xml = ElementTree.parse(urlopen(self.url_games + STEAM_URL_SUFFIX_XML)); xml_games = None
        for curr in xml.getroot():
            try:
                if curr.tag == 'steamID64':
                    self.steamID64 = curr.text
                if curr.tag == 'games':
                    xml_games = curr; break
            except:
                pass
        if xml_games is None:
            error_app(ERROR_LOAD_GAMES_FAILED)
        self.games_list = sorted(Game(xml_game) for xml_game in xml_games)
        self.games_map = {game.appID:game for game in self.games_list}

    # comparison functions
    def __lt__(self, o):
        return self.username.lower() < o.username.lower()
    def __le__(self, o):
        return self.username.lower() <= o.username.lower()
    def __gt__(self, o):
        return self.username.lower() > o.username.lower()
    def __ge__(self, o):
        return self.username.lower() >= o.username.lower()
    def __eq__(self, o):
        return self.username == o.username

    # user main page
    def view_main(self):
        text = '<ansired>- SteamID64:</ansired> %s' % self.steamID64
        if hasattr(self, 'real_name'):
            text += '\n<ansired>- Real Name:</ansired> %s' % self.real_name
        if hasattr(self, 'location'):
            text += '\n<ansired>- Location:</ansired> %s' % self.location
        if hasattr(self, 'member_since'):
            text += '\n<ansired>- Member Since:</ansired> %s' % self.member_since
        return radiolist_dialog(title='%s (%s)' % (self.username, self.online_state), text=HTML(text.strip()), values=[
            (self.view_library, HTML("<ansiblue>View Library</ansiblue> (%d games)" % len(self.games_list))),
            (self.view_achievements, HTML("<ansiblue>View Achievements</ansiblue>")),
        ]).run()

    # view games
    def view_games(self, mode):
        if mode == 'library':
            title = "%s's Library (%d games)" % (self.username, len(self.games_list))
        elif mode == 'achievements':
            title = "%s's Achievements" % self.username
        else:
            error_app(ERROR_INVALID_GAMES_LIST_MODE)
        game_list_dialog = radiolist_dialog(title=title, values=[(game,game.name) for game in self.games_list])
        while True:
            game_selection = game_list_dialog.run()
            if game_selection is None:
                break
            if mode == 'library':
                game_selection.view_details()
            elif mode == 'achievements':
                game_selection.view_achievements()
        return self.view_main
    def view_library(self):
        return self.view_games('library')
    def view_achievements(self):
        return self.view_games('achievements')

# main content
if __name__ == "__main__":
    # parse CLI arg (if applicable)
    username = None
    if len(argv) > 2 or (len(argv) == 2 and argv[1].lstrip('-').lower() in {'h','help'}):
        print("USAGE: %s [steam_username]" % argv[0]); exit(1)
    elif len(argv) == 2:
        username = argv[1].strip()

    # show welcome message and prompt user for Steam username
    if username is None:
        APPS['welcome'].run(); username = APPS['user_prompt'].run()
    if username is None or username == '':
        exit(1)

    # run app
    user = User(username); curr_view = user.view_main
    while curr_view is not None:
        curr_view = curr_view()
