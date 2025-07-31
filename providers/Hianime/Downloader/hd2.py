#/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# m3u8parser.py - This file contains the logic to parse M3U8 files and extract media streams.


import requests
import os
import m3u8
import time
import yt_dlp
from config.hianime import quality, parallel, logger, timeout, proxy_servers


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


def proxy(url: str, headers: dict, proxies: dict, timeout: int) -> requests.Response | None:
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


def m3u8_parsing(m3u8_dict):
    try:
        logger.info("Starting m3u8_parsing for: %s", m3u8_dict.get("id", {}).get("Title", "Unknown"))
        url = m3u8_dict["link"]["file"]
        subtitle = m3u8_dict["tracks"]
        intro = m3u8_dict["intro"]
        outro = m3u8_dict["outro"]
        logger.debug("URL: %s | Subtitles: %s | Intro: %s | Outro: %s", url, subtitle, intro, outro)
        m3u8_data = proxy(url, hd2_headers, proxy_servers, timeout)
        logger.info("Requested m3u8: %s | Status: %s", url, m3u8_data.status_code)
        playlist_str = m3u8_data.text
        m3u8_obj = m3u8.loads(playlist_str)
        Name = m3u8_dict["id"]["Title"]
        for playlist in m3u8_obj.playlists:
            stream_quality = f"{playlist.stream_info.resolution}".strip("()").replace(" ", "").split(",")[1]+"p"
            logger.debug("Checking stream quality: %s vs target: %s", stream_quality, quality)
            if quality == stream_quality:
                final_url = m3u8_dict["link"]["file"].replace('/master.m3u8', f'/{playlist.uri}')
                final_media = proxy(final_url, hd2_headers, proxy_servers, timeout)
                logger.info("Fetched final media: %s | Status: %s", final_media, final_media.status_code)
                return final_media.text, Name
        logger.warning("Requested quality %s not found", quality)
        return None, Name
    except Exception as e:
        logger.error("Exception in m3u8_parsing: %s", e, exc_info=True)
        return None, None
    
        
def downloading(segments, Name, Anime):
    try:
        logger.info("Starting download for %s in %s", Name, Anime)
        chars_to_remove = set(r'\/?"*|')
        fixed_Name = ''.join(ch for ch in Name if ch not in chars_to_remove)
        fixed_Anime = ''.join(ch for ch in Anime if ch not in chars_to_remove)
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
            'outtmpl': f"{fixed_Name}.mp4",
            'quiet': False,
            'no_warnings': True,
            'merge_output_format': 'mp4',
            'http_headers': hd2_headers,
            'enable_file_urls': True,
            'concurrent_fragment_downloads': parallel
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info("Starting yt_dlp download for %s", m3u8_path)
            ydl.download([f"file:///{cache}/{fixed_Name}.m3u8"])
        os.remove(f"{cache}/{fixed_Name}.m3u8")
        logger.info("Removed temporary .m3u8 file: %s", m3u8_path)
        return 0
    except Exception as e:
        logger.error("Exception in downloading function: %s", e, exc_info=True)
        return 1
        

        
    
    

