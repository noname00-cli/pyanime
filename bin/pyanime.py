#!/usr/env python3
# -*- coding: utf-8 -*-
# main.py  Main user interface for pyanime.


import shutil
import textwrap
from tabulate import tabulate
from providers.Hianime.Scraper.searchAnimeandetails import searchAnimeandetails


# Asthetics only!!! Don't give a damn about this!!!
def separator(type):
    terminal_size = shutil.get_terminal_size(fallback=(80, 24))
    separator_line = type * terminal_size.columns
    print(separator_line)


def wrap_text(text, width):
    if not isinstance(text, str):
        return text
    return '\n'.join(textwrap.wrap(text, width=width))


# Displaying the welcome message.
columns = shutil.get_terminal_size().columns
separator('=')
text = "Welcome to pyanime (v1.0.0)"
print(text.center(columns))
separator('=')


search = input("Name of anime: ")
search_results, important = searchAnimeandetails(search)

# Displaying the search results in a table format.
max_col_width = max(10, columns // len(search_results[0]))
for row in search_results:
    for key in row:
        row[key] = wrap_text(row[key], width=max_col_width)
table = tabulate(search_results, headers = "keys", tablefmt="grid")
print(table)
print("\n")


# Asking the user to select an anime from the search results.
separator('=')
if len(search_results) == 1:
    anime = search_results[0]
    stuff = important['Watch Link']
elif len(search_results) == 0:
    print("No anime found with that name.")
else:
    no = input("Enter the no of the anime you want to select: ")
    for anime in search_results:
        if anime['No'] == int(no):
            stuff = important['Watch Link']
            print(stuff)
            break
        
        

    

