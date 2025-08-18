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
from config.animekai import configure

# Setup logging for this module
logger = get_logger("scraper.searchEpisodedetails")


@log_function_call(logger)
@log_performance(logger)
def getanimepisode(watch_link):
    logger.info("Getting episode list for watch link: %s", watch_link)
    response = requests.get(watch_link, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    any_element = soup.find(attrs={'data-id': True})
    
    if any_element:
        logger.debug("Extracted episode ID: %s", any_element['data-id'])
        url = configure['baseurl']
        episodeurlapi = f"{url}/ajax/episode/list/{any_element['data-id']}"
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{watch_link}",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0',
            'Accept-Encoding': 'gzip, deflate, br',
        }
        
        try:
            logger.debug("Making request to episode API: %s", episodeurlapi)
            response = requests.get(episodeurlapi, headers=headers, verify=False)
            logger.debug("Response status: %d", response.status_code)
            
            data = response.json()
            
            # Check for 'result' field first, then 'html'
            html_content = None
            if 'result' in data:
                html_content = data['result']
                logger.debug("Using 'result' field from JSON response")
            elif 'html' in data:
                html_content = data['html']
                logger.debug("Using 'html' field from JSON response")
            else:
                logger.error("No HTML content in response for episode ID: %s", any_element['data-id'])
                return []
            
            # Unescape HTML entities
            import html
            unescaped_html = html.unescape(html_content)
            junk = BeautifulSoup(unescaped_html, 'html.parser')
            episodes = []
            
            # Look for the episode list items
            episode_elements = junk.find_all('li', {'title': True})
            logger.info("Found %d episode elements", len(episode_elements))
            
            for li_tag in episode_elements:
                ep = {}
                
                # Get episode title from li title attribute
                ep['Title'] = li_tag.get('title', '').strip()
                
                # Find the anchor tag within the li
                a_tag = li_tag.find('a')
                if a_tag:
                    ep['No'] = a_tag.get('data-num', '').strip()
                    ep['URL'] = a_tag.get('href', '').strip()
                    ep['Episode ID'] = a_tag.get('data-ids', '').strip()  # Note: data-ids not data-id
                    
                    # Get episode name and Japanese name from span
                    span_tag = a_tag.find('span', class_='d-title')
                    if span_tag:
                        ep['Episode Name'] = span_tag.get_text(strip=True).replace('\u2019', "'")
                        ep['Japanese Name'] = span_tag.get('data-jp', '').strip()
                    else:
                        ep['Episode Name'] = ep['Title']  # Fallback to title
                        ep['Japanese Name'] = ''
                    
                    # Additional data
                    ep['MAL ID'] = a_tag.get('data-mal', '').strip()
                    ep['Timestamp'] = a_tag.get('data-timestamp', '').strip()
                    ep['Watch Link'] = watch_link

                    
                else:
                    # If no anchor tag found, fill with defaults
                    ep['No'] = ''
                    ep['Episode Name'] = ep['Title']
                    ep['Japanese Name'] = ''
                    ep['URL'] = ''
                    ep['Episode ID'] = ''
                    ep['MAL ID'] = ''
                    ep['Timestamp'] = ''
                    ep['Watch Link'] = ''

                
                logger.debug("Extracted episode: %s (ID: %s)", ep['Title'], ep['Episode ID'])
                episodes.append(ep)
            
            logger.info("Successfully extracted %d episodes", len(episodes))
            return episodes
            
        except Exception as e:
            logger.error("Error processing episodes: %s", str(e))
            return []
    else:
        logger.error("No data-id found in watch page")
        return []


    




