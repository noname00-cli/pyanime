#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# main.py - Main user interface for pyanime.

import asyncio
import shutil
import textwrap
from tabulate import tabulate
from providers.Hianime.Scraper.searchAnimedetails import searchAnimeandetails, getAnimeDetails
from providers.Hianime.Scraper.searchEpisodedetails import getanimepisode
from providers.Hianime.Scraper.getEpisodestreams import serverextractor, streams
from providers.Hianime.Downloader.hd2 import m3u8_parsing, downloading
from config.hianime import subtitle

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
    
    # Get terminal size inside the function
    columns = shutil.get_terminal_size().columns
    max_col_width = max(10, columns // max_cols_in_row)
    return cleaned_results, max_col_width

def choose_servers(servers, needs):
    selected_servers = [s for s in servers if s['data_type'] == needs]
    if selected_servers:
        return selected_servers
    fallback_type = 'dub' if needs == 'sub' else 'sub'
    fallback_servers = [s for s in servers if s['data_type'] in (fallback_type, 'raw')]
    if fallback_servers:
        print(f"Falling back to {hex_to_rgb("#00fb8a", fallback_type)}.")
        print()
        return fallback_servers
    print("No servers available for needs or fallback.")
    return []

async def download_episode_async(episode, anime_title, needs):
    """Async function to download a single episode"""
    try:
        servers = serverextractor(episode)
        selected_servers = choose_servers(servers, needs)
        if not selected_servers:
            print(f"No servers found for episode {episode['Episode ID']}. Skipping.")
            return 1
        
        media = streams(selected_servers[0], episode)
        segments, name, subs = m3u8_parsing(media)

        if not segments:
            print(f"Failed to parse m3u8 for episode {episode['No']}. Skipping.")
            return 1
        
        separator("=")
        print(f"Downloading Episode {episode['No']}: {name}")
        
        # Extract base URL from media link if available
        base_url = None
        if 'link' in media and 'file' in media['link'] and media['link']['file'].startswith('http'):
            base_url = '/'.join(media['link']['file'].split('/')[:-1]) + '/'
            
        # Use async downloading with subtitle data and base URL
        code = await downloading(segments, f"{episode['No']}. {name}", anime_title, subs, base_url)
        
        if code == 1:
            print()
            print(f"{hex_to_rgb('#FF0000','Failed to download!!!')} Check for {hex_to_rgb('#73FF2E','pyanime.log')} in parent directory.")
            return 1
        elif code == 0:
            print()
            print(f"Episode {episode['No']} - {hex_to_rgb('#73FF2E','Downloaded successfully')}")
            return 0
            
    except Exception as e:
        print(f"Error downloading episode {episode['No']}: {e}")
        return 1

async def download_episodes_batch(selected_episodes, anime_title, needs):
    """Download multiple episodes with controlled concurrency"""
    print(hex_to_rgb("#fc861e","Starting batch download..."))
    print()
    
    success_count = 0
    failed_count = 0
    
    # Download episodes one by one to avoid overwhelming servers
    for episode in selected_episodes:
        result = await download_episode_async(episode, anime_title, needs)
        if result == 0:
            success_count += 1
        else:
            failed_count += 1
    
    # Summary
    separator("=")
    print(f"Download Summary:")
    print(f"  ✅ Successful: {hex_to_rgb('#73FF2E', str(success_count))}")
    print(f"  ❌ Failed: {hex_to_rgb('#FF0000', str(failed_count))}")
    
    return success_count, failed_count

async def main():
    """Main async function"""
    # Displaying the welcome message.
    separator('=')
    columns = shutil.get_terminal_size().columns
    text = "Welcome to pyanime (v1.0.0)"
    print(text.center(columns))

    separator('=')
    search = input("Name of anime: ")
    if search == "":
        print("No anime name provided.\nExiting...")
        separator('=')
        exit(1)
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
        exit(1)
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
    print()
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

    # Creating a table of the episodes of selected anime.
    separator('=')
    episode_list = getanimepisode(stuff)
    cleaned_anime, max_width = clean_result(["Episode ID", "URL"], episode_list)
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
    selection = input("Enter the episode number to select Hint:[1 / 1,2 / 1-10 ]: ")
    if selection:
        selected_episodes = []        
        if '-' in selection:
            start, end = map(int, selection.split('-'))
            selected_episodes = [ep for ep in episode_list if start <= int(ep["No"]) <= end]
        elif ',' in selection:
            selected_episodes = [ep for ep in episode_list if int(ep["No"]) in map(int, selection.split(','))]
        else:
            selected_episodes = [ep for ep in episode_list if int(ep["No"]) == int(selection)]

    separator('=')
    print(hex_to_rgb("#fc861e","Selected Episodes:"))
    print()
    sel_epi, max_width_epi = clean_result(["Episode ID", "URL"], selected_episodes)
    for row in sel_epi:
        for key in row:
            if key == "Title" or key == "Japanese name" or key == "Episode Name" :
                row[key] = wrap_text_with_color(row[key], "#1fa1d9", max_width_epi)
            elif key == "No":
                row[key] = wrap_text_with_color(row[key], "#ffea00", max_width_epi)
            else:
                # normal wrap (no color)
                row[key] = "\n".join(textwrap.wrap(str(row[key]), width=max_width_epi))
    table = tabulate(sel_epi, headers="keys", tablefmt="grid", colalign=("left", "right", "center"))
    print(table)
    print()

    separator('=')
    if subtitle == None:
        needs = input(f"Sub or Dub? [sub/dub]: ").strip().lower()
    else:
        needs = subtitle

    # Download episodes using async batch function
    success_count, failed_count = await download_episodes_batch(selected_episodes, anime_details['title'], needs)
    
    if failed_count > 0:
        print()
        print(f"{hex_to_rgb('#FF0000','Some downloads failed!')} Check for {hex_to_rgb('#73FF2E','pyanime.log')} in parent directory.")
        print()
    
    print()
    print(hex_to_rgb("#73FF2E","Download process completed!"))
    print("Exiting...")
    print()
    separator("=")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
