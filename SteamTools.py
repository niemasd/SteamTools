#! /usr/bin/env python3
'''
SteamTools (Niema Moshiri 2021)
'''

# error message
def error(s):
    print(s, file=stderr); exit(1)

# imports
from datetime import date, datetime
from glob import glob
from json import loads as jloads
from os import getcwd, makedirs
from os.path import abspath, expanduser, isfile, isdir
from sys import argv, stderr, stdout
from time import sleep
from urllib.request import Request, urlopen
from xml.etree import ElementTree
try:
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.shortcuts import input_dialog, message_dialog, radiolist_dialog
except:
    error("Unable to import 'prompt_toolkit'. Install via: 'pip install prompt_toolkit'")
try:
    from filedate import File
except:
    error("Unable to import 'filedate'. Install via: 'pip install filedate'")

# useful constants
VERSION = '0.0.2'
WINDOW_TITLE = HTML("<ansiblue>SteamTools v%s</ansiblue>" % VERSION)
ERROR_TITLE = HTML("<ansired>ERROR</ansired>")
LINE_WIDTH = 120
NUM_SHARED_FILE_ATTEMPTS = 10
REATTEMPT_DELAY = 0.5
URLLIB_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}

# URL stuff
STEAM_COMMUNITY_BASE_URL = "https://steamcommunity.com/id"
STEAM_APP_DETAILS_BASE_URL = "https://store.steampowered.com/api/appdetails?appids="
STEAM_SHARED_FILES_BASE_URL = "https://steamcommunity.com/sharedfiles/filedetails?id="
STEAM_URL_SUFFIX_XML = "?xml=1"

# messages
TEXT_LOADING_USER_DATA = "Loading user data"
TEXT_USER_PROMPT = "Please enter your Steam username:"
TEXT_NEW_DIR_PROMPT = "Enter new directory name:"
TEXT_WELCOME = "Welcome to SteamTools! This simple tool aims to provide a user-friendly command-line interface for exploring a public Steam account.\n\nMade by Niema Moshiri (niemasd), 2021"
TEXT_LOADING_SCREENSHOTS = "Loading screenshots from"
TEXT_LOADING_PAGE = "Loading page"
ERROR_IMPORT_PROMPT_TOOLKIT = "Unable to import 'prompt_toolkit'. Install via: 'pip install prompt_toolkit'"
ERROR_INVALID_USERNAME = "Please enter a valid Steam username"
ERROR_PROFILE_NOT_FOUND = "Profile not found"
ERROR_INVALID_GAME = "Invalid game"
ERROR_INVALID_GAMES_LIST_MODE = "Invalid games list mode"
ERROR_LOAD_DATA_FAILED = "Failed to load data"
ERROR_LOAD_GAMES_FAILED = "Failed to load game library"
ERROR_LOAD_SCREENSHOTS_FAILED = "Failed to load screenshots"
ERROR_FILE_EXISTS = "File exists"
ERROR_PATH_EXISTS = "Path exists"
ERROR_EMPTY_NAME = "Empty name"

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
    try:
        message_dialog(title=ERROR_TITLE, text=HTML(break_string("<ansired>ERROR:</ansired> %s" % s))).run()
    except:
        message_dialog(title=ERROR_TITLE, text=break_string("ERROR: %s" % s)).run()
    if crash:
        exit(1)

# select path app
def select_path_app(files=True, folders=True):
    curr_path = abspath(expanduser(getcwd()))
    while True:
        contents = sorted(glob('%s/*' % curr_path))
        values = [('.',HTML("<ansigreen>--- Select This Path ---</ansigreen>"))]
        values += [('', HTML("<ansiblue>- Create New Directory Here -</ansiblue>"))]
        if curr_path != '':
            values += [('..','..')]
        if folders:
            values += [(fn, fn.split('/')[-1] + '/') for fn in contents if isdir(fn)]
        if files:
            values += [(fn, fn.split('/')[-1]) for fn in contents if isfile(fn)]
        selection = radiolist_dialog(title=HTML("<ansiblue>Select Directory</ansiblue>"), text="Current: %s/" % curr_path, values=values).run()
        if selection is None:
            return None
        elif selection == '.':
            return curr_path
        elif selection == '..':
            curr_path = '/'.join(curr_path.split('/')[:-1])
        elif selection == '':
            while True:
                new_dir_name = input_dialog(title=HTML("<ansiblue>New Directory</ansiblue>"), text=TEXT_NEW_DIR_PROMPT).run()
                if new_dir_name is None:
                    break
                elif new_dir_name == '':
                    error_app(ERROR_EMPTY_NAME, crash=False)
                else:
                    new_dir_path = "%s/%s" % (curr_path, new_dir_name)
                    if isfile(new_dir_path) or isdir(new_dir_path):
                        error_app("%s: %s" % (ERROR_PATH_EXISTS, new_dir_path), crash=False)
                    else:
                        makedirs(new_dir_path); curr_path = new_dir_path; break
        else:
            curr_path = selection

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

# helper class to represent individual Steam Shared File
class SharedFile:
    # constructor
    def __init__(self, ID):
        self.ID = ID
        self.data = None

    # get file details URL
    def get_url_details(self):
        return "%s%d" % (STEAM_SHARED_FILES_BASE_URL, self.ID)

    # load data
    def load_data(self, overwrite=False):
        if self.data is not None and not overwrite:
            return
        self.data = dict(); url = self.get_url_details(); html_lines = None
        for _ in range(NUM_SHARED_FILE_ATTEMPTS): # try multiple times (sometimes fails on first try)
            try:
                html_lines = urlopen(Request(url,headers=URLLIB_HEADERS)).read().decode().splitlines(); break
            except:
                sleep(REATTEMPT_DELAY)
        if html_lines is None:
            error_app(ERROR_LOAD_DATA_FAILED, crash=False); self.data = None; return
        details_stats_names = list(); details_stats_vals = list()
        for i, l in enumerate(html_lines):
            if 'letterbox=false' in l:
                assert 'image_url' not in self.data, "Duplace image: %s" % url
                self.data['image_url'] = l.split('href="')[1].split('"')[0].strip()
            elif 'detailsStatsContainerLeft' in l:
                for j, jl in enumerate(html_lines[i+1:]):
                    jls = jl.strip()
                    if jls == '':
                        continue
                    elif jls == "</div>":
                        break
                    details_stats_names.append(jl.split('<div class="detailsStatLeft">')[1].split('</div>')[0].strip())
            elif 'detailsStatsContainerRight' in l:
                for j, jl in enumerate(html_lines[i+1:]):
                    jls = jl.strip()
                    if jls == '':
                        continue
                    elif jl.strip() == "</div>":
                        break
                    details_stats_vals.append(jl.split('<div class="detailsStatRight">')[1].split('</div>')[0].strip())
        assert len(details_stats_names) == len(details_stats_vals), "Failed to parse detail stats: %s" % url
        for i in range(len(details_stats_names)):
            self.data[details_stats_names[i]] = details_stats_vals[i]
        if 'Posted' in self.data:
            if ',' in self.data['Posted']: # has year
                self.data['Posted'] = datetime.strptime(self.data['Posted'], '%b %d, %Y @ %I:%M%p')
            else: # doesn't have year (meaning it's from this year)
                self.data['Posted'] = datetime.strptime(self.data['Posted'], '%b %d @ %I:%M%p').replace(year=date.today().year)

    # view file details
    def view_details(self):
        self.load_data()
        text = "<ansired>- URL (Details):</ansired> %s" % self.get_url_details()
        text += "\n<ansired>- Posted:</ansired> %s" % self.data['Posted']
        text += "\n<ansired>- Resolution:</ansired> %s" % self.data['Size']
        text += "\n<ansired>- File Size:</ansired> %s" % self.data['File Size']
        message_dialog(title=HTML("<ansiblue>%s</ansiblue>" % self.ID), text=HTML(text)).run()

    # download file
    def download(self, destination_path, overwrite=False):
        if isfile(destination_path) and not overwrite:
            error("%s: %s" % (ERROR_FILE_EXISTS, destination_path), crash=False)
        else:
            self.load_data(); data = None
            for _ in range(NUM_SHARED_FILE_ATTEMPTS): # try multiple times (sometimes fails on first try)
                try:
                    data = urlopen(Request(self.data['image_url'],headers=URLLIB_HEADERS)).read(); break
                except:
                    sleep(REATTEMPT_DELAY)
            if data is None:
                error_app(ERROR_LOAD_DATA_FAILED)
            f = open(destination_path, 'wb'); f.write(data); f.close()

    # str function
    def __str__(self):
        if self.data is None:
            return str(self.ID)
        else:
            return str((self.ID, self.data['Posted'], self.data['Size'], self.data['File Size']))

    # comparison functions
    def __lt__(self, o):
        return self.ID < o.ID
    def __le__(self, o):
        return self.ID <= o.ID
    def __gt__(self, o):
        return self.ID > o.ID
    def __ge__(self, o):
        return self.ID >= o.ID
    def __eq__(self, o):
        return type(self) == type(o) and self.ID == o.ID

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
        self.screenshots = None

    # load game details
    def load_details(self, overwrite=False):
        if self.details is not None and not overwrite:
            return
        try:
            self.details = jloads(urlopen(Request("%s%s" % (STEAM_APP_DETAILS_BASE_URL, self.appID),headers=URLLIB_HEADERS)).read().decode())[self.appID]['data']
        except:
            self.details = dict()
        if 'supported_languages' in self.details:
            self.details['supported_languages'] = self.details['supported_languages'].replace('<strong>','').replace('</strong>','').replace('<br>',', ').split(', ')

    # load game achievements
    def load_achievements(self, username, overwrite=False):
        if self.achievements is not None and not overwrite:
            return
        url = "%s/%s/stats/%s" % (STEAM_COMMUNITY_BASE_URL, username, self.appID)
        xml = ElementTree.parse(urlopen(Request(url + STEAM_URL_SUFFIX_XML,headers=URLLIB_HEADERS)))
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

    # load game screenshots
    def load_screenshots(self, username, overwrite=False):
        if self.screenshots is not None and not overwrite:
            return
        message("%s: %s" % (TEXT_LOADING_SCREENSHOTS, self.name))
        base_url = "%s/%s/screenshots?appid=%s" % (STEAM_COMMUNITY_BASE_URL, username, self.appID)
        base_url += "&sort=oldestfirst"
        base_url += "&browsefilter=myfiles"
        base_url += "&view=grid"
        base_url += "&p=" # will populate with page number in loop below
        self.screenshots = list()
        curr_page_num = 1; total_num_screenshots = None
        while total_num_screenshots is None or len(self.screenshots) < total_num_screenshots:
            url = "%s%d" % (base_url, curr_page_num)
            message("%s: %d" % (TEXT_LOADING_PAGE, curr_page_num), end='\r')
            html_lines = urlopen(Request(url,headers=URLLIB_HEADERS)).read().decode().splitlines()
            curr_page_screenshots = list()
            for _ in range(NUM_SHARED_FILE_ATTEMPTS): # try multiple times (sometimes fails on first try)
                curr_page_screenshots = [SharedFile(int(l.split('?id=')[1].split('"')[0])) for l in html_lines if 'filedetails' in l and '?id=' in l]
                if len(curr_page_screenshots) != 0:
                    break # successful download
                sleep(REATTEMPT_DELAY)
            if len(curr_page_screenshots) == 0:
                error_app("%s: %s\n%s" % (ERROR_LOAD_SCREENSHOTS_FAILED, self.name, url), crash=False)
                self.screenshots = None; return
            self.screenshots += curr_page_screenshots; curr_page_num += 1
            if total_num_screenshots is None:
                total_num_screenshots = int([l for l in html_lines if 'Showing ' in l][0].split(' of ')[1].split('<')[0])

    # view game details
    def view_details(self):
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

    # view game screenshots
    def view_screenshots(self, username=None):
        self.load_screenshots(username)
        if self.screenshots is None:
            return # loading screenshots failed
        values = [('download_all',HTML("<ansigreen>Download All</ansigreen>"))] + [(screenshot, str(screenshot.ID)) for screenshot in self.screenshots]
        screenshot_list_dialog = radiolist_dialog(title=HTML("<ansiblue>%s</ansiblue> <ansiblack>(%d screenshots)</ansiblack>" % (self.name, len(self.screenshots))), values=values)
        while True:
            screenshot_selection = screenshot_list_dialog.run()
            if screenshot_selection is None:
                break
            elif screenshot_selection == 'download_all':
                self.download_all_screenshots()
            else:
                screenshot_selection.view_details()

    # download all screenshots
    def download_all_screenshots(self):
        destination = select_path_app(files=False)
        if destination is None:
            return
        for i, screenshot in enumerate(self.screenshots):
            message("Downloading screenshot %d of %d" % (i+1, len(self.screenshots)), end='\r')
            screenshot.load_data(); posted_date = screenshot.data['Posted']
            out_path = "%s/%s_%s.jpg" % (destination, str(posted_date).replace(':','-').replace(' ','_'), screenshot.ID)
            screenshot.download(out_path); File(out_path).set(created=posted_date, modified=posted_date, accessed=posted_date)

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
        return type(self) == type(o) and self.appID == o.appID

# helper class to represent a user
class User:
    # constructor
    def __init__(self, username):
        # prepare for loading user data
        message(s="%s: %s" % (TEXT_LOADING_USER_DATA, username))
        url_community = "%s/%s" % (STEAM_COMMUNITY_BASE_URL, username)
        url_games = "%s/games" % url_community
        url_screenshots = "%s/screenshots" % url_community

        # load user data
        xml = ElementTree.parse(urlopen(Request(url_community + STEAM_URL_SUFFIX_XML,headers=URLLIB_HEADERS)))
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
        xml = ElementTree.parse(urlopen(Request(url_games + STEAM_URL_SUFFIX_XML,headers=URLLIB_HEADERS))); xml_games = None
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

        # load games with screenshots
        self.games_with_screenshots = {l.split("'appid': '")[1].split("'")[0] for l in urlopen(Request(url_screenshots,headers=URLLIB_HEADERS)).read().decode().splitlines() if 'javascript:SelectSharedFilesContentFilter' in l and 'appid' in l}

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
                (self.view_library, HTML("<ansiblue>Library</ansiblue> (%d games)" % len(self.games_list))),
                (self.view_achievements, HTML("<ansiblue>Achievements</ansiblue>")),
                (self.view_screenshots, HTML("<ansiblue>Screenshots</ansiblue> (%d games)" % len(self.games_with_screenshots))),
            ]).run()

    # view games
    def view_games(self, mode):
        if mode == 'library':
            title = HTML("<ansiblue>%s's Library</ansiblue> <ansiblack>(%d games)</ansiblack>" % (self.username, len(self.games_list)))
            values = [(game,game.name) for game in self.games_list]
        elif mode == 'achievements':
            title = HTML("<ansiblue>%s's Achievements</ansiblue>" % self.username)
            values = [(game,game.name) for game in self.games_list]
        elif mode == 'screenshots':
            title = HTML("<ansiblue>%s's Screenshots</ansiblue> <ansiblack>(%d games)</ansiblack>" % (self.username, len(self.games_with_screenshots)))
            values = [(game,game.name) for game in self.games_list if game.appID in self.games_with_screenshots]
        else:
            error_app(ERROR_INVALID_GAMES_LIST_MODE)
        game_list_dialog = radiolist_dialog(title=title, values=values)
        while True:
            game_selection = game_list_dialog.run()
            if game_selection is None:
                break
            if mode == 'library':
                game_selection.view_details()
            elif mode == 'achievements':
                game_selection.view_achievements(self.username)
            elif mode == 'screenshots':
                game_selection.view_screenshots(self.username)
        return self.view_main
    def view_library(self):
        return self.view_games('library')
    def view_achievements(self):
        return self.view_games('achievements')
    def view_screenshots(self):
        return self.view_games('screenshots')

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
