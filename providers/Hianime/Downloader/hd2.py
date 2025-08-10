#/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# m3u8parser.py - This file contains the logic to parse M3U8 files and extract media streams.

import sys
import os
import requests
import m3u8
import time
import yt_dlp

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from config.logging_config import get_logger, log_function_call, log_performance
from config.hianime import quality, parallel, timeout, proxy_servers

# Setup logging for this module
logger = get_logger("downloader.hd2")


hd2_headers = {
    'user-agent': "Mozilla/5.0 (X11; Linux aarch64; rv:122.0) Gecko/20100101 Firefox/122.0",
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.5',
    'origin': 'https://vidwish.live',
    'referer': 'https://vidwish.live/',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'te': 'trailers',
}


hd1_headers = {
    'user-agent': "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.5',
    'origin': 'https://megaplay.buzz',
    'referer': 'https://megaplay.buzz/',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'te': 'trailers',
}


@log_function_call(logger)
def proxy(url: str, headers: dict, proxies: dict, timeout: int) -> requests.Response | None:
    logger.debug("Making request to: %s", url)
    try:
        response = requests.get(url, headers=headers, timeout=timeout, proxies=None)
        logger.info("Request successful using native IP.")
        return response
    except (requests.Timeout, requests.ConnectionError) as e:
        logger.warning("Timeout or connection error using native IP: %s", e)
        logger.info("Waiting %d seconds before retrying with proxy...", timeout)
        time.sleep(timeout)
        try:
            response = requests.get(url, headers=headers, timeout=timeout, proxies=proxies)
            logger.info("Request successful using proxy.")
            return response
        except Exception as e2:
            logger.error("All attempts failed: %s", e2, exc_info=True)
            return None
    except Exception as e:
        logger.error("Unexpected error during m3u8 request: %s", e, exc_info=True)
        return None


@log_function_call(logger)
@log_performance(logger)
def m3u8_parsing(m3u8_dict):
    try:
        logger.info("Starting m3u8_parsing for: %s", m3u8_dict.get("id", {}).get("Title", "Unknown"))
        url = m3u8_dict["link"]["file"]
        subtitles = m3u8_dict["tracks"]
        intro = m3u8_dict["intro"]
        outro = m3u8_dict["outro"]
        logger.debug("URL: %s | Subtitles: %s | Intro: %s | Outro: %s", url, subtitles, intro, outro)
        m3u8_data = proxy(url, hd2_headers, proxy_servers, timeout)
        if m3u8_data is None:
            logger.error("Failed to fetch m3u8 data from: %s", url)
            return None, None
            
        logger.info("Requested m3u8: %s | Status: %d", url, m3u8_data.status_code)
        playlist_str = m3u8_data.text
        
        # Debug: Log the first few lines of the m3u8 content
        lines = playlist_str.split('\n')[:20]  # First 20 lines
        logger.debug("First 20 lines of m3u8 content:")
        for i, line in enumerate(lines):
            logger.debug("  Line %d: %s", i+1, line.strip())
        
        m3u8_obj = m3u8.loads(playlist_str)
        Name = m3u8_dict["id"]["Title"]
        
        logger.debug("Found %d playlists in m3u8", len(m3u8_obj.playlists))
        
        # First, try to find the requested quality
        requested_playlist = None
        available_qualities = []
        
        # Log all available qualities for debugging
        logger.info("Available qualities in m3u8:")
        for i, playlist in enumerate(m3u8_obj.playlists):
            stream_quality = f"{playlist.stream_info.resolution}".strip("()").replace(" ", "").split(",")[1]+"p"
            available_qualities.append((stream_quality, playlist))
            logger.info("  Quality %d: %s", i+1, stream_quality)
            logger.debug("Checking stream quality: %s vs target: %s", stream_quality, quality)
            if quality == stream_quality:
                requested_playlist = playlist
                break
        
        # If requested quality not found, select the highest available quality
        if requested_playlist is None:
            if available_qualities:
                # Sort by quality (higher resolution first)
                available_qualities.sort(key=lambda x: int(x[0].replace('p', '')), reverse=True)
                selected_quality, selected_playlist = available_qualities[0]
                logger.warning("Requested quality %s not found. Using highest available quality: %s", quality, selected_quality)
                requested_playlist = selected_playlist
            else:
                logger.error("No playlists found in m3u8")
                return None, Name
        
        # Use the selected playlist (either requested or fallback)
        final_url = m3u8_dict["link"]["file"].replace('/master.m3u8', f'/{requested_playlist.uri}')
        selected_quality = f"{requested_playlist.stream_info.resolution}".strip("()").replace(" ", "").split(",")[1]+"p"
        logger.info("Selected quality: %s, fetching final media from: %s", selected_quality, final_url)
        final_media = proxy(final_url, hd2_headers, proxy_servers, timeout)
        if final_media is None:
            logger.error("Failed to fetch final media from: %s", final_url)
            return None, Name
        logger.info("Fetched final media: %s | Status: %d", final_url, final_media.status_code)
        return final_media.text, Name
    except Exception as e:
        logger.error("Exception in m3u8_parsing: %s", e, exc_info=True)
        return None, None
    
        
@log_function_call(logger)
@log_performance(logger)
def downloading(segments, Name, Anime):
    try:
        logger.info("Starting download for %s in %s", Name, Anime)
        # More comprehensive character sanitization for file names
        chars_to_remove = set(r'\/?"*|<>:')
        fixed_Name = ''.join(ch for ch in Name if ch not in chars_to_remove)
        fixed_Anime = ''.join(ch for ch in Anime if ch not in chars_to_remove)
        
        # Replace spaces and other problematic characters
        fixed_Name = fixed_Name.replace(' ', '_').replace(',', '_').replace('.', '_')
        fixed_Anime = fixed_Anime.replace(' ', '_').replace(',', '_').replace('.', '_')
        logger.debug("Sanitized names - Name: %s, Anime: %s", fixed_Name, fixed_Anime)
        
        home_dir = os.path.expanduser("~")
        cache = f"{home_dir}/.animecache/{fixed_Anime}"
        os.makedirs(cache, exist_ok=True)
        logger.debug("Cache directory created at %s", cache)
        os.chdir(cache)
        m3u8_path = f"{fixed_Name}.m3u8"
        with open(m3u8_path, 'w', encoding='utf-8') as m3u8_writer:
            m3u8_writer.write(segments)
        logger.info("Wrote segments to %s", m3u8_path)
        ydl_opts = {
            'outtmpl': f"{fixed_Name}.mkv",
            'quiet': False,
            'no_warnings': True,
            'merge_output_format': 'mkv',
            'http_headers': hd2_headers,
            'enable_file_urls': True,
            'concurrent_fragment_downloads': parallel,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info("Starting yt_dlp download for %s", m3u8_path)
            try:
                # Use proper file URL format for Windows
                if os.name == 'nt':  # Windows
                    file_url = f"file:///{cache.replace(os.sep, '/')}/{fixed_Name}.m3u8"
                else:  # Unix/Linux/Mac
                    file_url = f"file://{cache}/{fixed_Name}.m3u8"
                logger.debug("Using file URL: %s", file_url)
                ydl.download([file_url])
            except Exception as e:
                logger.warning("File URL method failed: %s, trying alternative method", str(e))
                # Fallback: use relative path
                ydl.download([m3u8_path])
        os.remove(f"{cache}/{fixed_Name}.m3u8")
        logger.info("Removed temporary .m3u8 file: %s", m3u8_path)
        return 0
    except Exception as e:
        logger.error("Exception in downloading function: %s", e, exc_info=True)
        return 1
        

        
    
    

