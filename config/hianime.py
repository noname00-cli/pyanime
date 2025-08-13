#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# hianime.py - Configuration for HiAnime 
# This file contains settings for the HiAnime service, including constants.

from .logging_config import setup_logging, get_logger

# Setup logging for this module
logger = get_logger("config.hianime")


configure = {
    "baseurl": "https://hianime.bz",
    "baseurl_v2": "https://kaido.to",
    "providers": "https://megacloud.club",
    "headers": {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0"
    }
}
proxy_headers = {
    'user-agent': "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.5',
    'origin': configure["baseurl"],
    'referer': f'{configure["baseurl"]}/',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'te': 'trailers',
}
#key = "https://raw.githubusercontent.com/itzzzme/megacloud-keys/refs/heads/main/key.txt"
subtitle = "sub"        # Default subtitle language (sub/dub)
server_type = "hd-2"    # Possible values (hd-1/hd-2) hd-3 will be added in future
quality = "1080p"       # quality (1080p/720p/360p)
consume_data = "stream" # What do you want to do with this video (stream/watch)
player = "vlc"          # Favourite Player (vlc/mpv/iina)
parallel = 6            # ↑ increase number to get faster speeds (caveats: could get a temporary ip/device ban if continuous request sent)
timeout = 10            # giving time to parse the media urls 
proxy_servers = {}      # here we have proxy set but not working just for showpiece (hint: use vpn if u get an ip ban)
                        # search for "vpngate" or "vpnbook" for using with vpn.


# As of the current year 2025 hianime has
# these URLs:
# https://hianime.to    https://hianimez.is
# https://hianime.bz    https://hianime.cx
# https://hianime.tv    https://kaido.to
# https://hianime.nz    https://aniwatchtv.to
# https://hianime.pe    https://9animetv.to
#
# If you want to discover more URLs, you can 
# visit https://everythingmoe.com/ and can change 
# the baseurl and the providers URL to the one you want to use.
