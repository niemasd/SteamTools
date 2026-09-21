#! /usr/bin/env python3
'''
Download all of a given Steam user's screenshots for a given game. To find the game's app ID, go to the user's Screenshots page, click "Select a game", and pick the game:

https://steamcommunity.com/id/<USERNAME>/screenshots/
'''

# imports
from bs4 import BeautifulSoup
from datetime import date, datetime
from fake_useragent import UserAgent
from filedate import File
from pathlib import Path
from pickle import dump as pdump, load as pload
from time import sleep
from tqdm import tqdm
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import argparse

# constants
DEFAULT_REFERER = "https://steamcommunity.com"
DEFAULT_WAIT = 2

# helper class to keep track of download progress
class Progress:
    # load progress from file
    def __init__(self, pkl_path):
        self.pkl_path = pkl_path
        if pkl_path.exists():
            with open(pkl_path, mode='rb') as f:
                self.data = pload(f)
        else:
            self.data = dict()

    # save progress to file
    def save(self):
        with open(self.pkl_path, mode='wb') as f:
            pdump(self.data, f)

    # implement dict functionality
    def __len__(self):
        return len(self.data)
    def __contains__(self, key):
        return key in self.data
    def __str__(self):
        return str(self.data)
    def __getitem__(self, key):
        return self.data[key]
    def __setitem__(self, key, value):
        self.data[key] = value; self.save() # auto-save
    def __delitem__(self, key):
        del self.data[key]; self.save() # auto-save
    def keys(self):
        return self.data.keys()
    def values(self):
        return self.data.values()
    def items(self):
        return self.data.items()

# parse user args
def parse_args():
    # parse arguments
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-u', '--username', required=True, type=str, help="Steam Username")
    parser.add_argument('-a', '--appid', required=True, type=str, help="Game App ID")
    parser.add_argument('-o', '--output', required=True, type=str, help="Output Directory")
    parser.add_argument('-w', '--wait', required=False, type=float, default=DEFAULT_WAIT, help="Wait Before Request")
    parser.add_argument('-r', '--refresh', action='store_true', help="Refresh Loaded Game Data")
    parser.add_argument('--mkdir', action='store_true', help="Create Output Directory if Doesn't Exist")
    args = parser.parse_args()

    # check args before returning
    args.username = args.username.strip()
    args.appid = args.appid.strip()
    args.output = Path(args.output)
    if args.mkdir:
        args.output.mkdir(exist_ok=True)
    if not args.output.is_dir():
        raise ValueError(f"Output directory not found: {args.output}")
    return args

# download data from URL
def download(url, referer=DEFAULT_REFERER, wait=DEFAULT_WAIT):
    request = Request(url, headers={
        'User-Agent': UserAgent().random,
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': referer,
    })
    sleep(wait)
    try:
        with urlopen(request) as response:
            return response.read()
    except Exception as e:
        if isinstance(e, HTTPError) and e.code == 429:
            print(f"Encountered HTTP Error 429 (Too Many Requests): {url}\nWait a few minutes/hours and try again (progress will resume)."); exit(1)
        else:
            print(f"Error when downloading: {url}"); raise e

# download all screenshots
def download_screenshots(progress, wait=DEFAULT_WAIT):
    # set things up
    print(f"Downloading screenshots (user={progress['username']}, appid={progress['appid']})")
    screenshots_url = f"https://steamcommunity.com/id/{progress['username']}/screenshots/?appid={progress['appid']}&sort=oldestfirst&browsefilter=myfiles&view=grid"
    page_num = 1
    if 'num_pages' not in progress:
        progress['num_pages'] = float('inf')
    if 'num_screenshots' not in progress:
        progress['num_screenshots'] = float('inf')
    if 'screenshots' not in progress:
        progress['screenshots'] = set()

    # load list of screenshot IDs if not yet loaded
    if len(progress['screenshots']) != progress['num_screenshots']:
        with tqdm(desc="Parsing page number", total=progress['num_pages']) as pbar:
            while progress['num_pages'] is None or page_num <= progress['num_pages']:
                # load current screenshot page
                url = f"{screenshots_url}&p={page_num}"
                data = download(url, referer=screenshots_url, wait=wait)
                soup = BeautifulSoup(data.decode(), 'html.parser')

                # parse total number of screenshot pages if not yet loaded
                if not isinstance(progress['num_pages'], int):
                    try:
                        progress['num_pages'] = max(int(link.get_text()) for link in soup.find_all('a', class_='pagingPageLink'))
                    except Exception as e:
                        print(f"Failed to parse total number of pages: {url}"); raise e
                    pbar.total = progress['num_pages']

                # parse total number of screenshots if not yet loaded
                if not isinstance(progress['num_screenshots'], int):
                    try:
                        for tag in soup.find('div', id='image_wall').find_all('div'):
                            tag_text_lower = tag.get_text().strip().lower()
                            if tag_text_lower.startswith('showing'):
                                progress['num_screenshots'] = int(tag_text_lower.split(' of ')[-1].split()[0]); break
                        if not isinstance(progress['num_screenshots'], int):
                            raise ValueError(f"Failed to find '<div>Showing ? - ? of ???</div>'")
                    except Exception as e:
                        print(f"Failed to parse total number of screenshots: {url}"); raise e
                for thumb in soup.find_all('a', attrs={'data-publishedfileid':True}):
                    progress['screenshots'].add(int(thumb['data-publishedfileid']))
                progress.save(); page_num += 1; pbar.update(1)
    if len(progress['screenshots']) != progress['num_screenshots']:
        raise RuntimeError("Number of loaded screenshots does not match total number of screenshots")

    # download all screenshots
    for screenshot_id in tqdm(sorted(progress['screenshots'])):
        # set things up
        jpg_path = progress.pkl_path.parent / f'{screenshot_id}.jpg'
        if jpg_path.exists():
            continue

        # load details page
        details_url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={screenshot_id}"
        details_data = download(details_url, referer=screenshots_url, wait=wait)
        details_soup = BeautifulSoup(details_data.decode(), 'html.parser')

        # parse screenshot URL
        jpg_url = details_soup.find('div', class_='actualmediactn').find('a').get('href').split('?')[0].strip()
        if not jpg_url.startswith('http'):
            raise ValueError(f"Unable to load JPG URL ({jpg_url}): {details_url}")

        # parse screenshot timestamp
        posted_date = None
        details_block_vals = list(details_soup.find_all('div', class_='detailsStatRight'))
        for i, k in enumerate(details_soup.find_all('div', class_='detailsStatLeft')):
            if k.get_text().strip().lower().startswith('posted'):
                posted_date = details_block_vals[i].get_text().strip()
        if posted_date is None:
            raise ValueError(f"Unable to load posted date: {details_url}")
        if ',' in posted_date: # has year
            posted_date = datetime.strptime(posted_date, '%b %d, %Y @ %I:%M%p')
        else: # doesn't have year (so it's from this year)
            posted_date = datetime.strptime(posted_date, '%b %d @ %I:%M%p').replace(year=date.today().year)

        # download screenshot
        jpg_data = download(jpg_url, referer=details_url, wait=wait)
        with open(jpg_path, mode='wb') as f:
            f.write(jpg_data)
        File(jpg_path).set(created=posted_date, modified=posted_date, accessed=posted_date)

# main program logic
def main():
    args = parse_args()
    progress_pkl_path = args.output / f'progress.screenshots.{args.username}.{args.appid}.pkl'
    if args.refresh:
        progress_pkl_path.unlink(missing_ok=True)
    progress = Progress(progress_pkl_path)
    if 'username' not in progress:
        progress['username'] = args.username
    if 'appid' not in progress:
        progress['appid'] = args.appid
    download_screenshots(progress, wait=args.wait)

# run program
if __name__ == "__main__":
    main()
