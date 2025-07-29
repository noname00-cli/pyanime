#!/usr/env python3
# -*- coding: utf-8 -*-
# main.py - Main user interface for pyanime.


import json
import shutil
import textwrap
from tabulate import tabulate
from providers.Hianime.Scraper.searchAnimedetails import searchAnimeandetails, getAnimeDetails
from providers.Hianime.Scraper.searchEpisodedetails import getanimepisode


# Asthetics only!!! Don't give a damn about this!!!
def separator(type):
    terminal_size = shutil.get_terminal_size(fallback=(80, 24))
    separator_line = type * terminal_size.columns
    print(separator_line)


def wrap_text(text, width):
    if not isinstance(text, str):
        return text
    return '\n'.join(textwrap.wrap(text, width=width))

def hex_to_rgb(hex_code, text):
    hex_code = hex_code.lstrip("#")
    r, g, b=tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"


def wrap_text_with_color(text, hex_color, width):
    if not isinstance(text, str):
        text = str(text)
    wrapped_lines = textwrap.wrap(text, width=width)
    colored_lines = [hex_to_rgb(hex_color, line) for line in wrapped_lines]
    return "\n".join(colored_lines)


def clean_result(omit, results):
    cleaned_results = []
    for row in results:
        new_row = {k: v for k, v in row.items() if k not in omit}
        cleaned_results.append(new_row)
    max_cols_in_row = max(len(row) for row in cleaned_results)
    max_col_width = max(10, columns // max_cols_in_row)
    return cleaned_results, max_col_width

    
# Displaying the welcome message.
columns = shutil.get_terminal_size().columns
separator('=')
text = "Welcome to pyanime (v1.0.0)"
print(text.center(columns))
separator('=')


search = input("Name of anime: ")
if search == "":
    print("No anime name provided.\nExiting...")
    separator('=')
    exit(0)
else:
    search_results = searchAnimeandetails(search)


# Displaying the search results in a table format.
cleaned_results, max_col_width = clean_result(["Imp"], search_results)
for row in cleaned_results:
    for key in row:
        if key == "Title" or key == "Japanese Name" or key == "Type" or key == "Duration" or key == "Episodes" or key == "Subs" or key == "Dubs":
            row[key] = wrap_text_with_color(row[key], "#00b3ff", max_col_width)
        elif key == "No":
            row[key] = wrap_text_with_color(row[key], "#ffea00", max_col_width)
        else:
            # normal wrap (no color)
            row[key] = "\n".join(textwrap.wrap(str(row[key]), width=max_col_width))

table = tabulate(cleaned_results, headers="keys", tablefmt="grid", colalign=("left", "right", "center"))
print(table)
print()


# Asking the user to select an anime from the search results.
if len(search_results) == 1:
    anime = search_results[0]
    stuff = search_results[0]['Imp']['Watch Link']
elif len(search_results) == 0:
    print("No anime found with that name.\nExiting...")
    separator('=')
    exit(0)
else:
    separator('=')
    no = input("Enter the no of the anime you want to select: ")
    for anime in search_results:
        if anime['No'] == int(no):
            stuff = anime['Imp']['Watch Link']
            break


# Displaying the selected anime details.
separator('=')
anime_details = getAnimeDetails(stuff)
print(hex_to_rgb("#fc861e","Anime Details:"))
print(f"\tTitle: {hex_to_rgb("#75e64c",anime_details['title'])}")
if 'Synonyms' in anime_details['details'] and anime_details['details']['Synonyms']:
    print(f"\tJapanese Name: {hex_to_rgb("#75e64c",anime_details['details']['Synonyms'])}")
else:
    print(f"\tJapanese Name: {hex_to_rgb("#75e64c",anime_details['title'])}")
print(f"\tIn Japanese: {hex_to_rgb("#75e64c",anime_details['details']['Japanese'])}")
print(f"\tDuration: {hex_to_rgb("#75e64c",anime_details['details']['Duration'])}")
print(f"\tAge Rating: {hex_to_rgb("#75e64c",anime_details['age'])}")
print(f"\tQuality: {hex_to_rgb("#75e64c",anime_details['quality'])}")
print(f"\tAir Date: {hex_to_rgb("#75e64c",anime_details['details']['Aired'])}")
if anime_details['details']['Status'] == "Finished Airing":
    print(f"\tStatus: {hex_to_rgb("#00fb8a",anime_details['details']['Status'])}")
elif anime_details['details']['Status'] == "Currently Airing":
    print(f"\tStatus: {hex_to_rgb("#ffb84d",anime_details['details']['Status'])}")
else:
    print(f"\tStatus: {hex_to_rgb("#ff0000",anime_details['details']['Status'])}")
print(f"\tGenres: {hex_to_rgb("#75e64c",anime_details['details']['Genres'])}")
if 'Producers' in anime_details['details'] and anime_details['details']['Producers']:
    print(f"\tProducers: {hex_to_rgb("#75e64c",anime_details['details']['Producers'])}")
else:
    print(f"\tProducers: {hex_to_rgb("#ff0000","Not Available")}")
print(f"\tStudio: {hex_to_rgb("#75e64c",anime_details['details']['Studios'])}")
terminalsize=shutil.get_terminal_size(fallback=(80, 24))
terminal_width = terminalsize.columns
print(f"\tSynopsis: {wrap_text(hex_to_rgb("#88ae15",anime_details['details']['Overview']), width=terminal_width)}")
separator('=')


# Creating a table of the episodes of selected anime.
episodes = getanimepisode(stuff)
cleaned_anime, max_width = clean_result(["Episode ID", "URL"], episodes)
for row in cleaned_anime:
    for key in row:
        if key == "Title" or key == "Japanese name" or key == "Episode Name" :
            row[key] = wrap_text_with_color(row[key], "#1fa1d9", max_width)
        elif key == "No":
            row[key] = wrap_text_with_color(row[key], "#ffea00", max_width)
        else:
            # normal wrap (no color)
            row[key] = "\n".join(textwrap.wrap(str(row[key]), width=max_width))
table = tabulate(cleaned_anime, headers="keys", tablefmt="grid", colalign=("left", "right", "center"))
print(table)
print()
separator('=')


# Asking the user to select episodes from the list.







        
        

    

