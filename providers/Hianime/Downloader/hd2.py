#/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# m3u8parser.py - This file contains the logic to parse M3U8 files and extract media streams.


import requests
import m3u8
from config.hianime import quality


hd2_headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0',
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

    # Access variants
    for playlist in m3u8_obj.playlists:
        if quality == f"{playlist.stream_info.resolution}".strip("()").replace(" ", "").split(",")[1]+"p":
            final_url = m3u8_dict["link"]["file"].replace('/master.m3u8', f'/{playlist.uri}')
            final_media = requests.get(final_url, headers=hd2_headers)
            m3u8_obj2 = m3u8.loads(final_media.text)
            segment_urls = [segment.uri for segment in m3u8_obj2.segments]
            return segment_urls
        

#def downloading():

            


    
    
        # print(f"URI: {final_url}")
        # print(f"Bandwidth: {playlist.stream_info.bandwidth}")
        # print(f"Resolution: {playlist.stream_info.resolution}")
        # print(f"Codecs: {playlist.stream_info.codecs}")
        # print(f"Frame Rate: {playlist.stream_info.frame_rate}")
        # print('---')
    
    

