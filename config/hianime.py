#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# hianime.py - Configuration for HiAnime 
# This file contains settings for the HiAnime service, including constants.

configure = {
    "baseurl": "https://hianime.bz",
    "baseurl_v2": "https://kaido.to",
    "providers": "https://megacloud.club",
    "headers": {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0"
    }
}
proxy_headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Referer": configure["baseurl"]
}
key = "https://raw.githubusercontent.com/itzzzme/megacloud-keys/refs/heads/main/key.txt"

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
