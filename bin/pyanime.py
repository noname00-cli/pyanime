#!/usr/env python3
# -*- coding: utf-8 -*-
# main.py - Main user interface for pyanime.

import sys
import os
import shutil
import textwrap
import time
from tabulate import tabulate

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.logging_config import setup_logging, get_logger, log_function_call, log_performance
from providers.Hianime.Scraper.searchAnimedetails import searchAnimeandetails, getAnimeDetails
from providers.Hianime.Scraper.searchEpisodedetails import getanimepisode
from providers.Hianime.Scraper.getEpisodestreams import serverextractor, streams
from providers.Hianime.Downloader.hd2 import m3u8_parsing, downloading
from config.hianime import subtitle
from utils.terminal_utils import print_section_header

# Setup logging for the main application
logger = get_logger("main")


# Asthetics only!!! Don't give a damn about this!!!
@log_function_call(logger)
def separator(type="=", message=None, log_level="info"):
    """
    Create a visual separator line for terminal output.
    
    Args:
        type (str): Character to use for separator (default: "=")
        message (str): Optional message to display in center of separator
        log_level (str): Log level for the separator (debug, info, warning, error)
    """
    terminal_size = shutil.get_terminal_size(fallback=(80, 24))
    separator_line = type * terminal_size.columns
    
    if message:
        # Calculate padding to center the message
        padding = (terminal_size.columns - len(message) - 2) // 2
        if padding > 0:
            separator_line = type * padding + " " + message + " " + type * (terminal_size.columns - padding - len(message) - 2)
        else:
            separator_line = type * 2 + " " + message + " " + type * 2
    
    # Log the separator creation
    if log_level == "debug":
        logger.debug("Creating separator line with type: %s, length: %d", type, len(separator_line))
    elif log_level == "warning":
        logger.warning("Creating separator line with type: %s, length: %d", type, len(separator_line))
    elif log_level == "error":
        logger.error("Creating separator line with type: %s, length: %d", type, len(separator_line))
    else:
        logger.info("Creating separator line with type: %s, length: %d", type, len(separator_line))
    
    print(separator_line)


@log_function_call(logger)
def wrap_text(text, width):
    if not isinstance(text, str):
        logger.debug("Converting non-string text to string: %s", type(text))
        return text
    wrapped = '\n'.join(textwrap.wrap(text, width=width))
    logger.debug("Wrapped text from %d chars to %d lines", len(text), len(wrapped.split('\n')))
    return wrapped

@log_function_call(logger)
def hex_to_rgb(hex_code, text):
    hex_code = hex_code.lstrip("#")
    r, g, b=tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
    colored_text = f"\033[38;2;{r};{g};{b}m{text}\033[0m"
    logger.debug("Applied color RGB(%d,%d,%d) to text: %s", r, g, b, text[:50] + "..." if len(text) > 50 else text)
    return colored_text


@log_function_call(logger)
def wrap_text_with_color(text, hex_color, width):
    if not isinstance(text, str):
        logger.debug("Converting non-string text to string: %s", type(text))
        text = str(text)
    wrapped_lines = textwrap.wrap(text, width=width)
    colored_lines = [hex_to_rgb(hex_color, line) for line in wrapped_lines]
    result = "\n".join(colored_lines)
    logger.debug("Wrapped and colored text: %d lines, color: %s", len(wrapped_lines), hex_color)
    return result


@log_function_call(logger)
def clean_result(omit, results):
    logger.info("Cleaning results: omitting fields %s from %d results", omit, len(results))
    cleaned_results = []
    for row in results:
        new_row = {k: v for k, v in row.items() if k not in omit}
        cleaned_results.append(new_row)
    max_cols_in_row = max(len(row) for row in cleaned_results)
    columns = shutil.get_terminal_size().columns
    max_col_width = max(10, columns // max_cols_in_row)
    logger.debug("Cleaned results: %d rows, max columns: %d, max width: %d", len(cleaned_results), max_cols_in_row, max_col_width)
    return cleaned_results, max_col_width


@log_function_call(logger)
def choose_servers(servers, needs):
    logger.info("Choosing servers for needs: %s from %d available servers", needs, len(servers))
    selected_servers = [s for s in servers if s['data_type'] == needs]
    if selected_servers:
        logger.info("Found %d servers matching needs: %s", len(selected_servers), needs)
        return selected_servers
    fallback_type = 'dub' if needs == 'sub' else 'sub'
    fallback_servers = [s for s in servers if s['data_type'] in (fallback_type, 'raw')]
    if fallback_servers:
        print(f"Falling back to {hex_to_rgb("#00fb8a", fallback_type)}.")
        print()
        logger.info("Found %d fallback servers", len(fallback_servers))
        return fallback_servers
    logger.error("No servers available for needs or fallback")
    print("No servers available for needs or fallback.")
    return []


@log_function_call(logger)
def print_progress_bar(current, total, prefix="Progress", width=50, color="#00ff00"):
    """Print a progress bar with percentage."""
    if total == 0:
        return
    
    progress = int((current / total) * width)
    bar = "█" * progress + "░" * (width - progress)
    percentage = int((current / total) * 100)
    
    progress_text = f"{prefix}: [{bar}] {percentage}% ({current}/{total})"
    colored_progress = hex_to_rgb(color, progress_text)
    print(f"\r{colored_progress}", end="", flush=True)
    
    if current == total:
        print()  # New line when complete


@log_function_call(logger)
def format_anime_table(results):
    """Format anime search results with better column widths and wrapping."""
    if not results:
        return []
    
    # Calculate optimal column widths based on content
    terminal_width = shutil.get_terminal_size().columns
    min_col_width = 8
    max_col_width = 25
    
    # Define column priorities (lower number = higher priority)
    columns = [
        ('No', 1, 4),
        ('Title', 2, 20),
        ('Japanese Name', 3, 18),
        ('Type', 4, 6),
        ('Duration', 5, 8),
        ('Episodes', 6, 8),
        ('Subs', 7, 6),
        ('Dubs', 8, 6)
    ]
    
    # Calculate available width for content columns
    fixed_width = sum(width for _, _, width in columns)
    available_width = terminal_width - fixed_width - (len(columns) * 3)  # Account for table borders
    
    # Distribute available width to content columns
    content_columns = [col for col in columns if col[1] in [2, 3]]  # Title and Japanese Name
    if content_columns and available_width > 0:
        extra_width = available_width // len(content_columns)
        for i, (name, priority, width) in enumerate(columns):
            if priority in [2, 3]:  # Title and Japanese Name
                columns[i] = (name, priority, min(max_col_width, width + extra_width))
    
    formatted_results = []
    for row in results:
        formatted_row = {}
        for key, value in row.items():
            if key == 'No':
                formatted_row[key] = hex_to_rgb("#ffea00", str(value))
            elif key in ['Title', 'Japanese Name']:
                # Find the column width for this key
                col_width = next((col[2] for col in columns if col[0] == key), 15)
                formatted_row[key] = wrap_text_with_color(str(value), "#00b3ff", col_width)
            elif key in ['Type', 'Duration', 'Episodes', 'Subs', 'Dubs']:
                formatted_row[key] = hex_to_rgb("#75e64c", str(value))
            else:
                formatted_row[key] = str(value)
        formatted_results.append(formatted_row)
    
    return formatted_results


@log_function_call(logger)
def format_episode_table(episodes):
    """Format episode list with better information display."""
    if not episodes:
        return []
    
    formatted_episodes = []
    for episode in episodes:
        formatted_episode = {}
        for key, value in episode.items():
            if key == 'No':
                formatted_episode[key] = hex_to_rgb("#ffea00", str(value))
            elif key in ['Title', 'Episode Name', 'Japanese name']:
                formatted_episode[key] = hex_to_rgb("#1fa1d9", str(value))
            else:
                formatted_episode[key] = str(value)
        formatted_episodes.append(formatted_episode)
    
    return formatted_episodes


# Displaying the welcome message.
logger.info("Starting pyanime application")
print_section_header("Welcome to pyanime (v1.0.0)")
logger.debug("Terminal width: %d columns", shutil.get_terminal_size().columns)

# Set up signal handler for graceful Ctrl+C handling
def signal_handler(signum, frame):
    print()
    print(f"{hex_to_rgb('#ffaa00', '⚠️  Interrupted by user (Ctrl+C)')}")
    print(f"{hex_to_rgb('#00b3ff', 'Gracefully shutting down...')}")
    logger.info("Application interrupted by user (Ctrl+C)")
    print()
    separator("=", "Interrupted", "warning")
    print(f"{hex_to_rgb('#75e64c', 'Thank you for using pyanime!')}")
    print("Exiting...")
    print()
    separator("=")
    sys.exit(0)

import signal
signal.signal(signal.SIGINT, signal_handler)

print(f"{hex_to_rgb('#00b3ff', 'Enter the name of the anime you want to search for:')}")
search = input("Name of anime: ")
logger.info("User search query: %s", search)
if search == "":
    logger.warning("No anime name provided by user")
    print("No anime name provided.\nExiting...")
    separator('=', "Exiting", "warning")
    exit(1)
else:
    logger.info("Searching for anime: %s", search)
    print(f"{hex_to_rgb('#00b3ff', 'Searching...')}")
    search_results = searchAnimeandetails(search)


# Displaying the search results in a table format.
logger.info("Displaying search results: %d results found", len(search_results))
if search_results:
    print(f"\n{hex_to_rgb('#fc861e', f'Found {len(search_results)} anime:')}")
    print()
    
    cleaned_results, max_col_width = clean_result(["Imp"], search_results)
    formatted_results = format_anime_table(cleaned_results)
    
    table = tabulate(formatted_results, headers="keys", tablefmt="grid", colalign=("center", "left", "left", "center", "center", "center", "center", "center"))
    print(table)
    print()
    logger.debug("Search results table displayed with %d rows", len(cleaned_results))
else:
    print(f"{hex_to_rgb('#ff0000', 'No results found.')}")
    separator('=', "No Results", "warning")
    exit(1)


# Asking the user to select an anime from the search results.
if len(search_results) == 1:
    logger.info("Single anime found, auto-selecting: %s", search_results[0]['Title'])
    anime = search_results[0]
    stuff = search_results[0]['Imp']['Watch Link']
    print(f"{hex_to_rgb('#00ff00', 'Auto-selected:')} {hex_to_rgb('#00b3ff', anime['Title'])}")
elif len(search_results) == 0:
    logger.warning("No anime found for search query: %s", search)
    print("No anime found with that name.\nExiting...")
    separator('=')
    exit(1)
else:
    logger.info("Multiple anime found, requesting user selection")
    separator('=')
    print(f"{hex_to_rgb('#ffaa00', 'Multiple anime found. Please select one:')}")
    no = input("Enter the no of the anime you want to select: ")
    logger.info("User selected anime number: %s", no)
    try:
        selected_no = int(no)
        for anime in search_results:
            if anime['No'] == selected_no:
                logger.info("Selected anime: %s", anime['Title'])
                stuff = anime['Imp']['Watch Link']
                print(f"{hex_to_rgb('#00ff00', 'Selected:')} {hex_to_rgb('#00b3ff', anime['Title'])}")
                break
        else:
            print(f"{hex_to_rgb('#ff0000', 'Invalid selection. Exiting...')}")
            exit(1)
    except ValueError:
        print(f"{hex_to_rgb('#ff0000', 'Invalid input. Please enter a number.')}")
        exit(1)


# Displaying the selected anime details.
separator('=')
logger.info("Fetching anime details for: %s", anime['Title'])
print(f"{hex_to_rgb('#00b3ff', 'Fetching anime details...')}")
anime_details = getAnimeDetails(stuff)
logger.info("Anime details retrieved successfully")

if anime_details:
    print(f"\n{hex_to_rgb('#fc861e', 'Anime Details:')}")
    print()
    print(f"\t{hex_to_rgb('#75e64c', 'Title:')} {hex_to_rgb('#00b3ff', anime_details['title'])}")
    if 'Synonyms' in anime_details['details'] and anime_details['details']['Synonyms']:
        print(f"\t{hex_to_rgb('#75e64c', 'Japanese Name:')} {hex_to_rgb('#00b3ff', anime_details['details']['Synonyms'])}")
    else:
        print(f"\t{hex_to_rgb('#75e64c', 'Japanese Name:')} {hex_to_rgb('#00b3ff', anime_details['title'])}")
    print(f"\t{hex_to_rgb('#75e64c', 'In Japanese:')} {hex_to_rgb('#00b3ff', anime_details['details']['Japanese'])}")
    print(f"\t{hex_to_rgb('#75e64c', 'Duration:')} {hex_to_rgb('#00b3ff', anime_details['details']['Duration'])}")
    print(f"\t{hex_to_rgb('#75e64c', 'Age Rating:')} {hex_to_rgb('#00b3ff', anime_details['age'])}")
    print(f"\t{hex_to_rgb('#75e64c', 'Quality:')} {hex_to_rgb('#00b3ff', anime_details['quality'])}")
    print(f"\t{hex_to_rgb('#75e64c', 'Air Date:')} {hex_to_rgb('#00b3ff', anime_details['details']['Aired'])}")
    
    status = anime_details['details']['Status']
    if status == "Finished Airing":
        print(f"\t{hex_to_rgb('#75e64c', 'Status:')} {hex_to_rgb('#00fb8a', status)}")
    elif status == "Currently Airing":
        print(f"\t{hex_to_rgb('#75e64c', 'Status:')} {hex_to_rgb('#ffb84d', status)}")
    else:
        print(f"\t{hex_to_rgb('#75e64c', 'Status:')} {hex_to_rgb('#ff0000', status)}")
    
    print(f"\t{hex_to_rgb('#75e64c', 'Genres:')} {hex_to_rgb('#00b3ff', anime_details['details']['Genres'])}")
    
    if 'Producers' in anime_details['details'] and anime_details['details']['Producers']:
        print(f"\t{hex_to_rgb('#75e64c', 'Producers:')} {hex_to_rgb('#00b3ff', anime_details['details']['Producers'])}")
    else:
        print(f"\t{hex_to_rgb('#75e64c', 'Producers:')} {hex_to_rgb('#ff0000', 'Not Available')}")
    
    if 'Studio' in anime_details['details'] and anime_details['details']['Studio']:
        print(f"\t{hex_to_rgb('#75e64c', 'Studio:')} {hex_to_rgb('#00b3ff', anime_details['details']['Studio'])}")
    else:
        print(f"\t{hex_to_rgb('#75e64c', 'Studio:')} {hex_to_rgb('#ff0000', 'Not Available')}")
    
    terminalsize = shutil.get_terminal_size(fallback=(80, 24))
    terminal_width = terminalsize.columns
    print(f"\t{hex_to_rgb('#75e64c', 'Synopsis:')} {wrap_text(hex_to_rgb('#88ae15', anime_details['details']['Overview']), width=terminal_width-15)}")
    logger.debug("Anime details displayed: %s", anime_details['title'])
else:
    print(f"{hex_to_rgb('#ff0000', 'Failed to fetch anime details.')}")
    exit(1)



# Creating a table of the episodes of selected anime.
separator('=')
logger.info("Fetching episode list for anime: %s", anime_details['title'])
print(f"{hex_to_rgb('#00b3ff', 'Fetching episode list...')}")
episode_list = getanimepisode(stuff)
logger.info("Episode list retrieved: %d episodes found", len(episode_list))

if episode_list:
    print(f"\n{hex_to_rgb('#fc861e', f'Episode List ({len(episode_list)} episodes):')}")
    print()
    
    cleaned_anime, max_width = clean_result(["Episode ID", "URL"], episode_list)
    formatted_episodes = format_episode_table(cleaned_anime)
    
    table = tabulate(formatted_episodes, headers="keys", tablefmt="grid", colalign=("center", "left", "left", "left"))
    print(table)
    print()
    logger.debug("Episode list displayed with %d episodes", len(episode_list))
else:
    print(f"{hex_to_rgb('#ff0000', 'No episodes found.')}")
    exit(1)


separator('=', "Episode Selection", "info")
print(f"{hex_to_rgb('#ffaa00', 'Select episodes to download:')}")
print(f"{hex_to_rgb('#00b3ff', 'Format examples:')}")
print(f"  {hex_to_rgb('#75e64c', 'Single:')} 1")
print(f"  {hex_to_rgb('#75e64c', 'Multiple:')} 1,2,5")
print(f"  {hex_to_rgb('#75e64c', 'Range:')} 1-10")
print(f"  {hex_to_rgb('#75e64c', 'All:')} all")
print()

selection = input("Enter the episode number to select: ")
logger.info("User episode selection: %s", selection)

if selection.lower() == 'all':
    selected_episodes = episode_list
    logger.info("Selected all episodes: %d episodes", len(selected_episodes))
elif selection:
    selected_episodes = []        
    if '-' in selection:
        try:
            start, end = map(int, selection.split('-'))
            logger.info("Range selection: episodes %d to %d", start, end)
            selected_episodes = [ep for ep in episode_list if start <= int(ep["No"]) <= end]
        except ValueError:
            print(f"{hex_to_rgb('#ff0000', 'Invalid range format. Use: start-end (e.g., 1-10)')}")
            exit(1)
    elif ',' in selection:
        try:
            episode_numbers = list(map(int, selection.split(',')))
            logger.info("Multiple selection: episodes %s", episode_numbers)
            selected_episodes = [ep for ep in episode_list if int(ep["No"]) in episode_numbers]
        except ValueError:
            print(f"{hex_to_rgb('#ff0000', 'Invalid multiple format. Use: 1,2,3')}")
            exit(1)
    else:
        try:
            episode_number = int(selection)
            logger.info("Single selection: episode %d", episode_number)
            selected_episodes = [ep for ep in episode_list if int(ep["No"]) == episode_number]
        except ValueError:
            print(f"{hex_to_rgb('#ff0000', 'Invalid input. Please enter a number.')}")
            exit(1)
    
    logger.info("Selected %d episodes for download", len(selected_episodes))
else:
    print(f"{hex_to_rgb('#ff0000', 'No selection made. Exiting...')}")
    exit(1)

if not selected_episodes:
    print(f"{hex_to_rgb('#ff0000', 'No valid episodes selected. Exiting...')}")
    exit(1)


separator('=', "Selected Episodes", "info")
logger.info("Displaying selected episodes")
print(f"{hex_to_rgb('#fc861e', f'Selected Episodes ({len(selected_episodes)}):')}")
print()

sel_epi, max_width_epi = clean_result(["Episode ID", "URL"], selected_episodes)
formatted_selected = format_episode_table(sel_epi)
table = tabulate(formatted_selected, headers="keys", tablefmt="grid", colalign=("center", "left", "left", "left"))
print(table)
print()
logger.debug("Selected episodes table displayed")


separator('=', "Download Configuration", "info")
if subtitle == None:
    print(f"{hex_to_rgb('#ffaa00', 'Choose audio preference:')}")
    needs = input(f"Sub or Dub? [sub/dub]: ").strip().lower()
    logger.info("User selected subtitle preference: %s", needs)
    if needs not in ['sub', 'dub']:
        print(f"{hex_to_rgb('#ff0000', 'Invalid choice. Defaulting to sub.')}")
        needs = 'sub'
else:
    needs = subtitle
    logger.info("Using default subtitle preference: %s", needs)

print(f"{hex_to_rgb('#00ff00', f'Using: {needs.upper()}')}")
print()

logger.info("Starting download process for %d episodes", len(selected_episodes))
print(f"{hex_to_rgb('#fc861e', f'Starting download process for {len(selected_episodes)} episode(s)...')}")
print(f"{hex_to_rgb('#00b3ff', 'This may take some time depending on the number of episodes and your internet speed.')}")
print()
for episode in selected_episodes:
    servers = serverextractor(episode)
    selected_servers = choose_servers(servers, needs)
    if not selected_servers:
        print(f"No servers found for episode {episode['Episode ID']}. Skipping.")
        continue
    #print(selected_servers)
    media = streams(selected_servers[0], episode)
    media, name = m3u8_parsing(media)
    separator("=")
    code = downloading(media, f"{episode["No"]}. {name}", anime_details['title'])
    if code == 1:
        print()
        print(f"{hex_to_rgb("#FF0000","Failed to download!!!")} Check for {hex_to_rgb("#73FF2E","pyanime.log")} in parent directory.")
        print("Exiting...")
        print()
        separator("=")
        exit(1)
    elif code == 0:
        separator("=")
        print()
        print(hex_to_rgb("#73FF2E","Done"))
        print("Exiting...")
        print()
        separator("=")








    






    
        
    
   






        
        

    

