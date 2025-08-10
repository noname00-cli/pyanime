#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# searchEpisodedetails.py - This file contains the logic to extract episode details from a given anime ID.

import sys
import os
import requests
from bs4 import BeautifulSoup

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from config.logging_config import get_logger, log_function_call, log_performance
from config.hianime import configure

# Setup logging for this module
logger = get_logger("scraper.searchEpisodedetails")


@log_function_call(logger)
@log_performance(logger)
def getanimepisode(watch_link):
    logger.info("Getting episode list for watch link: %s", watch_link)
    episodeid = watch_link.replace('/watch/', '').split("-")[-1]
    logger.debug("Extracted episode ID: %s", episodeid)
    
    url = configure['baseurl']
    episodeurlapi = f"{url}/ajax/v2/episode/list/{episodeid}"
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{url}{watch_link}"
    }
    
    try:
        logger.debug("Making request to episode API: %s", episodeurlapi)
        response = requests.get(episodeurlapi, headers=headers)
        logger.debug("Response status: %d", response.status_code)
        
        data = response.json()
        if 'html' not in data:
            logger.error("No HTML content in response for episode ID: %s", episodeid)
            return 0
            
        junk = BeautifulSoup(data['html'], 'html.parser')
        episodes = []
        
        episode_elements = junk.select('a.ssl-item.ep-item')
        logger.info("Found %d episode elements", len(episode_elements))
        
        for a_tag in episode_elements:
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
            
            logger.debug("Extracted episode: %s (ID: %s)", ep['Title'], ep['Episode ID'])
            episodes.append(ep)
            
        logger.info("Successfully extracted %d episodes", len(episodes))
        return episodes
        
    except Exception as e:
        logger.error("Error getting episode list: %s", str(e), exc_info=True)
        return []

    




