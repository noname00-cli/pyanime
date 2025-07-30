#/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# m3u8parser.py - This file contains the logic to parse M3U8 files and extract media streams.


import requests
import os
import m3u8
import yt_dlp
from config.hianime import quality


hd2_headers = {
    'user-agent': "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.5',
    'origin': 'https://vidwish.live',
    'referer': 'https://vidwish.live/',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'te': 'trailers',
}


def m3u8_parsing(m3u8_dict):
    url = m3u8_dict["link"]["file"]
    subtitle = m3u8_dict["tracks"]
    intro = m3u8_dict["intro"]
    outro = m3u8_dict["outro"]
    m3u8_data = requests.get(url, headers=hd2_headers)
    playlist_str = m3u8_data.text
    m3u8_obj = m3u8.loads(playlist_str)
    Name = m3u8_dict["id"]["Title"]

    # Access variants
    for playlist in m3u8_obj.playlists:
        if quality == f"{playlist.stream_info.resolution}".strip("()").replace(" ", "").split(",")[1]+"p":
            final_url = m3u8_dict["link"]["file"].replace('/master.m3u8', f'/{playlist.uri}')
            final_media = requests.get(final_url, headers=hd2_headers)
            return final_media.text, Name
    
        
def downloading(segments, Name, Anime):
    chars_to_remove = set(r'\/?"*|')
    fixed_Name = ''.join(ch for ch in Name if ch not in chars_to_remove)
    fixed_Anime = ''.join(ch for ch in Anime if ch not in chars_to_remove)
    home_dir = os.path.expanduser("~")
    cache = f"{home_dir}/.animecache/{fixed_Anime}"
    os.makedirs(cache, exist_ok=True)
    os.chdir(cache)
    with open(f"{fixed_Name}.m3u8", 'w',encoding='utf-8') as m3u8_writer:
        m3u8_writer.write(segments)
    ydl_opts = {
        'outtmpl': f"{fixed_Name}.mp4",  # Output filename or template
        'quiet': False,                  # Set to True for silent download
        'no_warnings': True,
        'merge_output_format': 'mp4',
        'http_headers': hd2_headers,
        'enable_file_urls': True,
        'concurrent_fragment_downloads': 16  
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"file:///{cache}/{fixed_Name}.m3u8"])
        os.remove(f"{cache}/{fixed_Name}.m3u8")
        m3u8_writer.close()

        





            


    
    
        # print(f"URI: {final_url}")
        # print(f"Bandwidth: {playlist.stream_info.bandwidth}")
        # print(f"Resolution: {playlist.stream_info.resolution}")
        # print(f"Codecs: {playlist.stream_info.codecs}")
        # print(f"Frame Rate: {playlist.stream_info.frame_rate}")
        # print('---')
    
    

