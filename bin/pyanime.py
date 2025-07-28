#!/usr/env python3
# -*- coding: utf-8 -*-
# main.py  Main user interface for pyanime.


import shutil
from providers.Hianime.Scraper.searchAnimeandetails import searchAnimeandetails


# Asthetics only!!! Don't give a damn about this!!!
def separator():
    terminal_size = shutil.get_terminal_size(fallback=(80, 24))
    separator_line = '=' * terminal_size.columns
    print(separator_line)


# Displaying the welcome message.
columns = shutil.get_terminal_size().columns
separator()
text = "Welcome to pyanime (v1.0.0)"
print(text.center(columns))
separator()


search = input("Name of anime: ")
search_results = searchAnimeandetails(search)
print(search_results)