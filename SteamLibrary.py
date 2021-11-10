#! /usr/bin/env python3
'''
SteamLibrary (Niema Moshiri 2021)
'''

# imports
from prompt_toolkit.shortcuts import message_dialog

# useful constants
WINDOW_TITLE = "SteamLibrary - Niema Moshiri"
STEAM_COMMUNITY_BASE_URL = "https://steamcommunity.com/id"

# welcome message
def welcome_message():
  return message_dialog(title=WINDOW_TITLE, text="hola")

# main content
if __name__ == "__main__":
  # show welcome message
  welcome_message()
