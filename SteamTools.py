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
from random import uniform
from sys import argv, stderr, stdout
from time import monotonic, sleep
from urllib.error import HTTPError, URLError
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
try:
    from tqdm import tqdm
except:
     error("Unable to import 'tqdm'. Install via: 'pip install tqdm'")

# useful constants
VERSION = '0.0.4'
WINDOW_TITLE = HTML("<ansiblue>SteamTools v%s</ansiblue>" % VERSION)
ERROR_TITLE = HTML("<ansired>ERROR</ansired>")
LINE_WIDTH = 120
NUM_SHARED_FILE_ATTEMPTS = 10
MIN_REQUEST_INTERVAL = 2.0
INITIAL_BACKOFF = 30.0
MAX_BACKOFF = 300.0
LAST_STEAM_REQUEST = 0.0
URLLIB_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}

# URL stuff
STEAM_COMMUNITY_BASE_URL = "https://steamcommunity.com/id"
STEAM_APP_DETAILS_BASE_URL = "https://store.steampowered.com/api/appdetails?appids="
STEAM_SHARED_FILES_BASE_URL = "https://steamcommunity.com/sharedfiles/filedetails?id="

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

# clean an HTML string
def clean_html(s):
    s = s.strip()
    s = s.replace('&', '&amp;')
    return s

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
        message_dialog(title=ERROR_TITLE, text=HTML("<ansired>ERROR:</ansired> %s" % s)).run()
    except:
        message_dialog(title=ERROR_TITLE, text=("ERROR: %s" % s)).run()
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

# helper function to download something from Steam
def steam_get(url, attempts=NUM_SHARED_FILE_ATTEMPTS):
    global LAST_STEAM_REQUEST
    backoff = INITIAL_BACKOFF
    for attempt in range(attempts):
        elapsed = monotonic() - LAST_STEAM_REQUEST
        wait = MIN_REQUEST_INTERVAL - elapsed
        if wait > 0:
            sleep(wait + uniform(0, 0.5))
        LAST_STEAM_REQUEST = monotonic()
        try:
            with urlopen(Request(url, headers=URLLIB_HEADERS)) as response:
                return response.read()
        except HTTPError as e:
            if e.code != 429 and not (500 <= e.code < 600):
                raise
            retry_after = e.headers.get('Retry-After')
            if retry_after and retry_after.is_digit():
                wait = max(float(retry_after), MIN_REQUEST_INTERVAL)
            else:
                wait = min(backoff, MAX_BACKOFF) + uniform(0, 2)
                backoff = min(backoff * 2, MAX_BACKOFF)
            if e.code == 429:
                print("Steam rate limit (429). Waiting %.0f seconds before retry..." % wait)
            else:
                print("Steam server error (%d). Waiting %.0f seconds before retry..." % (e.code, wait))
            sleep(wait)
        except URLError as e:
            wait = min(backoff, MAX_BACKOFF) + uniform(0, 2)
            backoff = min(backoff * 2, MAX_BACKOFF)
            print("Network error: %s. Waiting %.0f seconds before retry..." % (e, wait))
            sleep(wait)
    return None

# apps
APPS = {
    'welcome': message_dialog(title=WINDOW_TITLE, text=TEXT_WELCOME),
    'user_prompt': input_dialog(title=WINDOW_TITLE, text=TEXT_USER_PROMPT)
}

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
        self.data = dict(); url = self.get_url_details()
        try:
            html_lines = steam_get(url).decode().splitlines()
        except:
            error_app('%s\n%s' % (ERROR_LOAD_DATA_FAILED, url), crash=False); self.data = None; return
        details_stats_names = list(); details_stats_vals = list()
        for i, l in enumerate(html_lines):
            if 'letterbox=false' in l:
                assert 'image_url' not in self.data, "Duplicate image: %s" % url
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
            self.load_data()
            if self.data is None:
                return
            data = steam_get(self.data['image_url'])
            if data is None:
                error_app(ERROR_LOAD_DATA_FAILED); return
            with open(destination_path, mode='wb') as f:
                f.write(data)

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

# helper class to represent a user
class User:
    # constructor
    def __init__(self, username):
        # initialize instance variables
        self.games = dict() # self.games[app_id] = {'title': game title}
        self.screenshots = dict() # self.screenshots[app_id] = list of screenshots

        # prepare for loading user data
        message(s="%s: %s" % (TEXT_LOADING_USER_DATA, username))
        url_community = "%s/%s" % (STEAM_COMMUNITY_BASE_URL, username)
        url_games = "%s/games" % url_community
        url_screenshots = "%s/screenshots" % url_community

        # load user data
        xml = ElementTree.parse(urlopen(Request(url_community + "?xml=1",headers=URLLIB_HEADERS)))
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
        return radiolist_dialog(title=title, text=text, values=[
            (self.view_screenshots_user, HTML("<ansiblue>Screenshots</ansiblue>")),
        ]).run()

    # view games for this user
    def view_games(self, mode):
        if mode == 'screenshots':
            title = HTML("<ansiblue>%s's Screenshots</ansiblue> <ansiblack>(%d games)</ansiblack>" % (self.username, len(self.screenshots)))
            values = [(app_id,self.games[app_id]['title']) for app_id in sorted(self.screenshots.keys(), key=lambda x: self.games[x]['title'].lower())]
        else:
            error_app(ERROR_INVALID_GAMES_LIST_MODE)
        game_list_dialog = radiolist_dialog(title=title, values=values)
        while True:
            app_id = game_list_dialog.run()
            if app_id is None:
                break
            self.view_screenshots(app_id)
        return self.view_main

    # view user's screenshots
    def view_screenshots_user(self):
        self.load_screenshot_games()
        return self.view_games('screenshots')

    # load list of games user has screenshots in
    def load_screenshot_games(self, overwrite=False):
        if (len(self.screenshots) != 0) and (not overwrite):
            return
        message("%s: %s" % (TEXT_LOADING_SCREENSHOTS, self.username))
        base_url = "%s/%s/screenshots" % (STEAM_COMMUNITY_BASE_URL, username)
        html_lines = [l.strip() for l in urlopen(Request(base_url,headers=URLLIB_HEADERS)).read().decode().splitlines()]
        for l in html_lines:
            if 'javascript:SelectSharedFilesContentFilter' in l:
                if "'appid':" not in l:
                    continue
                app_id = l.split("'appid':")[-1].split("'")[1].strip()
                if app_id == '0':
                    continue
                title = l.split('});">')[1].replace('</div>','')
                self.games[app_id] = {'title':title}
                self.screenshots[app_id] = None # will be filled by self.load_screenshots(app_id)

    # load user's screenshots for specific game
    def load_screenshots(self, app_id, overwrite=False):
        if (self.screenshots[app_id] is not None) and (not overwrite):
            return
        message("%s: %s" % (TEXT_LOADING_SCREENSHOTS, self.games[app_id]['title']))
        base_url = "%s/%s/screenshots?appid=%s" % (STEAM_COMMUNITY_BASE_URL, self.username, app_id)
        base_url += "&sort=oldestfirst"
        base_url += "&browsefilter=myfiles"
        base_url += "&view=grid"
        base_url += "&p=" # will populate with page number in loop below
        curr_game_screenshots = list()
        curr_page_num = 1; total_num_screenshots = None
        while total_num_screenshots is None or len(curr_game_screenshots) < total_num_screenshots:
            url = "%s%d" % (base_url, curr_page_num)
            message("%s: %d" % (TEXT_LOADING_PAGE, curr_page_num), end='\r')
            curr_page_screenshots = list()
            try:
                html_lines = steam_get(url).decode().splitlines()
                curr_page_screenshots = [SharedFile(int(l.split('?id=')[1].split('"')[0])) for l in html_lines if 'filedetails' in l and '?id=' in l]
                assert len(curr_page_screenshots) != 0
            except Exception as e:
                error_app("%s: %s\n%s\n\n%s" % (ERROR_LOAD_SCREENSHOTS_FAILED, self.games[app_id]['title'], url, e), crash=False); return
            curr_game_screenshots += curr_page_screenshots; curr_page_num += 1
            if total_num_screenshots is None:
                total_num_screenshots = int([l for l in html_lines if 'Showing ' in l][0].split(' of ')[1].split('<')[0])
        self.screenshots[app_id] = sorted(curr_game_screenshots)

    # view user's screenshots for specific game
    def view_screenshots(self, app_id):
        self.load_screenshots(app_id)
        if (self.screenshots[app_id] is None) or (len(self.screenshots[app_id]) == 0):
            return # no screenshots
        values = [('download_all',HTML("<ansigreen>Download All</ansigreen>"))] + [(screenshot, str(screenshot.ID)) for screenshot in self.screenshots[app_id]]
        title_str = clean_html("<ansiblue>%s</ansiblue> <ansiblack>(%d screenshots)</ansiblack>" % (self.games[app_id]['title'], len(self.screenshots[app_id])))
        screenshot_list_dialog = radiolist_dialog(title=HTML(title_str), values=values)
        while True:
            screenshot_selection = screenshot_list_dialog.run()
            if screenshot_selection is None:
                break
            elif screenshot_selection == 'download_all':
                self.download_all_screenshots(app_id)
            else:
                screenshot_selection.view_details()

    # download all screenshots for a specific game
    def download_all_screenshots(self, app_id):
        destination = select_path_app(files=False)
        if destination is None:
            return
        for i, screenshot in tqdm(enumerate(self.screenshots[app_id]), total=len(self.screenshots[app_id])):
            screenshot.load_data()
            if screenshot.data is None:
                print(f"Failed to download: {screenshot}"); return # early exit if failed to download
            posted_date = screenshot.data['Posted']
            out_path = "%s/%s_%s.jpg" % (destination, str(posted_date).replace(':','-').replace(' ','_'), screenshot.ID)
            if isfile(out_path):
                print(f"{out_path} already exists. Skipping..."); continue
            screenshot.download(out_path); File(out_path).set(created=posted_date, modified=posted_date, accessed=posted_date)

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
