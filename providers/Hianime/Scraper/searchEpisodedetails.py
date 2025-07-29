#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# searchEpisodedetails.py - This file contains the logic to extract episode details from a given anime ID.


import requests
from bs4 import BeautifulSoup
from config.hianime import configure


def getanimepisode(watch_link):
    episodeid = watch_link.replace('/watch/', '').split("-")[-1]
    url = configure['baseurl']
    episodeurlapi = f"{url}/ajax/v2/episode/list/{episodeid}"
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{url}{watch_link}"
    }
    response = requests.get(episodeurlapi, headers=headers)
    data = response.json()
    if 'html' not in data:
        return 0
    junk = BeautifulSoup(data['html'], 'html.parser')
    episodes = []
    for a_tag in junk.select('a.ssl-item.ep-item'):
        ep = {}
        ep['No'] = a_tag.get('data-number', '').strip()
        ep['Title'] = a_tag.get('title', '').strip()
        ep_name_div = a_tag.select_one('div.ep-name.e-dynamic-name')
        if ep_name_div:
            ep['Episode Name'] = ep_name_div.get_text(strip=True).replace('\u2019', "'")  # fix encoded apostrophe
            ep['Japanese name'] = ep_name_div.get('data-jname', '').strip()
        else:
            ep['Episode Name'] = ''
            ep['Japanese Name'] = ''
        ep['URL'] = a_tag.get('href', '').strip()
        ep['Episode ID'] = a_tag.get('data-id', '').strip()
            
        episodes.append(ep)
    return episodes

    




