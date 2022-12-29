#! /usr/bin/env python3
'''
SteamTools (Niema Moshiri 2021)
'''

# error message
def error(s):
    print(s, file=stderr); exit(1)

# imports
from datetime import datetime
from json import loads as jloads
from sys import argv, stderr, stdout
from urllib.request import urlopen
from xml.etree import ElementTree
try:
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.shortcuts import input_dialog, message_dialog, radiolist_dialog
except:
    error("Unable to import 'prompt_toolkit'. Install via: 'pip install prompt_toolkit'")

# useful constants
VERSION = '0.0.1'
WINDOW_TITLE = HTML("<ansiblue>SteamTools v%s</ansiblue>" % VERSION)
ERROR_TITLE = HTML("<ansired>ERROR</ansired>")
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
ERROR_INVALID_USERNAME = "Please enter a valid Steam username"
ERROR_PROFILE_NOT_FOUND = "Profile not found"
ERROR_INVALID_GAME = "Invalid game"
ERROR_INVALID_GAMES_LIST_MODE = "Invalid games list mode"
ERROR_LOAD_GAMES_FAILED = "Failed to load game library"

# message
def message(s='', end='\n'):
    print(s, end=end); stdout.flush()

# message app
def message_app(s):
    message_dialog(title=WINDOW_TITLE, text=s).run()

# error message
def error(s, crash=True):
    print(s, file=stderr)
    if crash:
        exit(1)

# error message app
def error_app(s, crash=True):
    message_dialog(title=ERROR_TITLE, text=HTML(break_string("<ansired>ERROR:</ansired> %s" % s))).run()
    if crash:
        exit(1)

# break a long string into multiple lines
def break_string(s, max_width=LINE_WIDTH):
    col = 0; text = ''
    for word in s.split(' '):
        if col + len(word) + 1 >= max_width:
            text += '\n'; col = 0
        text += (word + ' '); col += (len(word) + 1)
    return text

# apps
APPS = {
    'welcome': message_dialog(title=WINDOW_TITLE, text=TEXT_WELCOME),
    'user_prompt': input_dialog(title=WINDOW_TITLE, text=TEXT_USER_PROMPT)
}

# helper class to represent individual achievements
class Achievement:
    # constructor
    def __init__(self, achievement):
        self.unlock_time = None # None = still locked
        for curr in achievement:
            if curr.tag == 'iconClosed':
                self.url_icon_unlocked = curr.text.strip()
            elif curr.tag == 'iconOpen':
                self.url_icon_locked = curr.text.strip()
            elif curr.tag == 'name':
                self.name = curr.text.strip()
            elif curr.tag == 'apiname':
                self.name_api = curr.text.strip()
            elif curr.tag == 'description':
                self.description = curr.text.strip()
            elif curr.tag == 'unlockTimestamp':
                self.unlock_time = datetime.utcfromtimestamp(int(curr.text))

    # view achievement details
    def view_details(self):
        if self.unlock_time is None:
            text = '<ansired>Locked</ansired>'
        else:
            text = '<ansigreen>Unlocked %s GMT</ansigreen>' % self.unlock_time
        text += '\n\n%s' % break_string(self.description)
        message_dialog(title=HTML("<ansiblue>%s</ansiblue>" % self.name), text=HTML(text)).run()

    # str function
    def __str__(self):
        return str(self.__dict__)

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
        self.achievements = None

    # load game details
    def load_details(self):
        try:
            self.details = jloads(urlopen("%s%s" % (STEAM_APP_DETAILS_BASE_URL, self.appID)).read().decode())[self.appID]['data']
        except:
            self.details = dict()
        if 'supported_languages' in self.details:
            self.details['supported_languages'] = self.details['supported_languages'].replace('<strong>','').replace('</strong>','').replace('<br>',', ').split(', ')

    # load game achievements
    def load_achievements(self, username):
        url = "%s/%s/stats/%s" % (STEAM_COMMUNITY_BASE_URL, username, self.appID)
        xml = ElementTree.parse(urlopen(url + STEAM_URL_SUFFIX_XML))
        xml_stats = None; xml_achievements = None
        for curr in xml.getroot():
            try:
                #if curr.tag == 'stats':
                #    xml_stats = curr
                if curr.tag == 'achievements':
                    xml_achievements = curr; break
            except:
                pass
        self.achievements = [Achievement(curr) for curr in xml_achievements]


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
            text += break_string(self.details['short_description'])
        message_dialog(title=HTML("<ansiblue>%s</ansiblue>" % self.name), text=HTML(text.strip())).run()

    # view game achievements
    def view_achievements(self, username=None):
        if self.achievements is None:
            self.load_achievements(username)
        locked = list(); unlocked = list()
        for achievement in self.achievements:
            if achievement.unlock_time is None:
                locked.append((achievement, HTML('<ansired>%s</ansired>' % achievement.name)))
            else:
                unlocked.append((achievement, HTML('<ansigreen>%s</ansigreen>' % achievement.name)))
        achievement_list_dialog = radiolist_dialog(title=HTML("<ansiblue>%s</ansiblue> <ansiblack>(<ansigreen>%d</ansigreen>/%d)</ansiblack>" % (self.name, len(unlocked), len(self.achievements))), values=unlocked+locked)
        while True:
            achievement_selection = achievement_list_dialog.run()
            if achievement_selection is None:
                break
            achievement_selection.view_details()

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
        url_community = "%s/%s" % (STEAM_COMMUNITY_BASE_URL, username)
        url_games = "%s/games" % url_community

        # load user data
        xml = ElementTree.parse(urlopen(url_community + STEAM_URL_SUFFIX_XML))
        for curr in xml.getroot():
            try:
                if curr.tag == 'steamID':
                    self.username = curr.text.strip()
                elif curr.tag == 'steamID64':
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
        xml = ElementTree.parse(urlopen(url_games + STEAM_URL_SUFFIX_XML)); xml_games = None
        for curr in xml.getroot():
            if curr.tag == 'error':
                error_app(curr.text.strip())
            try:
                if curr.tag == 'games':
                    xml_games = curr; break
            except Exception as e:
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
        online_state_color = {True:'green', False:'red'}[self.online_state == 'Online']
        title=HTML('<ansiblue>%s (<ansi%s>%s</ansi%s>)</ansiblue>' % (self.username, online_state_color, self.online_state, online_state_color))
        text = '<ansired>- SteamID64:</ansired> %s' % self.steamID64
        if hasattr(self, 'real_name'):
            text += '\n<ansired>- Real Name:</ansired> %s' % self.real_name
        if hasattr(self, 'location'):
            text += '\n<ansired>- Location:</ansired> %s' % self.location
        if hasattr(self, 'member_since'):
            text += '\n<ansired>- Member Since:</ansired> %s' % self.member_since
        text = HTML(text.strip())
        if len(self.games_list) == 0:
            message_dialog(title=title, text=text).run()
        else:
            return radiolist_dialog(title=title, text=text, values=[
                (self.view_library, HTML("<ansiblue>View Library</ansiblue> (%d games)" % len(self.games_list))),
                (self.view_achievements, HTML("<ansiblue>View Achievements</ansiblue>")),
            ]).run()

    # view games
    def view_games(self, mode):
        if mode == 'library':
            title = HTML("<ansiblue>%s's Library</ansiblue> <ansiblack>(%d games)</ansiblack>" % (self.username, len(self.games_list)))
        elif mode == 'achievements':
            title = HTML("<ansiblue>%s's Achievements</ansiblue>" % self.username)
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
                game_selection.view_achievements(self.username)
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
        APPS['welcome'].run(); username = ''
        while True:
            username = APPS['user_prompt'].run()
            if username is None:
                break
            username = username.strip()
            if username == '':
                error_app(ERROR_INVALID_USERNAME, crash=False)
            else:
                break
    if username is None or username == '':
        exit(1)

    # run app
    user = User(username); curr_view = user.view_main
    while curr_view is not None:
        curr_view = curr_view()
