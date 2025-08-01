#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
logger = get_logger("scraper.searchAnimedetails")


@log_function_call(logger)
@log_performance(logger)
def searchAnimeandetails(name):
    logger.info("Searching for anime: %s", name)
    list_of_anime = []
    No = 0
    url = configure['baseurl']
    
    try:
        logger.debug("Making request to: %s/search?keyword=%s", url, name)
        html = requests.get(f'{url}/search?keyword={name}'.format(search=name), auth=('user', 'pass'))
        logger.debug("Response status: %d", html.status_code)
        
        soup = BeautifulSoup(html.text, 'html.parser')
        anime_blocks = soup.find_all('div', class_='flw-item')
        logger.info("Found %d anime blocks in search results", len(anime_blocks))
        
        for block in anime_blocks:
            No += 1

            # Extract basic info
            title_tag = block.find('h3', class_='film-name').find('a')
            title = title_tag.get('title', '').strip()
            japanese_name = title_tag.get('data-jname', '').strip()

            # Type and Duration - span elements in fd-infor div
            fd_infor = block.find('div', class_='fd-infor')
            if fd_infor:
                type_span = fd_infor.find('span', class_='fdi-item')
                type_ = type_span.text.strip() if type_span else 'N/A'

                duration_span = fd_infor.find('span', class_='fdi-duration')
                duration = duration_span.text.strip() if duration_span else 'N/A'
            else:
                type_ = 'N/A'
                duration = 'N/A'

            # Image URL
            img_tag = block.find('img', class_='film-poster-img')
            image_url = img_tag.get('data-src', '').strip() if img_tag else 'N/A'

            # Watch Link
            watch_a = block.find('a', class_='film-poster-ahref')
            watch_link = watch_a.get('href', '').strip() if watch_a else 'N/A'

            # Episode/Sub/Dub info in div.tick-item inside div.tick
            tick_div = block.find('div', class_='tick ltr')
            if tick_div:
                sub_div = tick_div.find('div', class_='tick-item tick-sub')
                sub_episodes = sub_div.text.strip() if sub_div and sub_div.text.strip() else 'N/A'

                dub_div = tick_div.find('div', class_='tick-item tick-dub')
                dub_episodes = dub_div.text.strip() if dub_div and dub_div.text.strip() else 'N/A'

                eps_div = tick_div.find('div', class_='tick-item tick-eps')
                total_episodes = eps_div.text.strip() if eps_div and eps_div.text.strip() else 'N/A'
            else:
                sub_episodes = 'N/A'
                dub_episodes = 'N/A'
                total_episodes = 'N/A'

            anime_details = {
                'No': No,
                'Title': title,
                'Japanese Name': japanese_name,
                'Type': type_,
                'Duration': duration,
                'Episodes': total_episodes,
                'Subs': sub_episodes,
                'Dubs': dub_episodes,
                'Imp' : {
                    'Watch Link': watch_link,
                    'Image URL': image_url,
                }       
            }

            logger.debug("Extracted anime details: %s (No: %d)", title, No)
            list_of_anime.append(anime_details)
    
        logger.info("Search completed. Found %d anime results", len(list_of_anime))
        return list_of_anime
    
    except Exception as e:
        logger.error("Error during anime search: %s", str(e), exc_info=True)
        return []


@log_function_call(logger)
@log_performance(logger)
def getAnimeDetails(watch_link):
    logger.info("Getting anime details for watch link: %s", watch_link)
    watch_link = watch_link.replace('/watch/', '/')
    url = configure['baseurl']
    
    try:
        logger.debug("Making request to: %s%s", url, watch_link)
        html = requests.get(f'{url}{watch_link}', auth=('user', 'pass'))
        logger.debug("Response status: %d", html.status_code)
        
        soup = BeautifulSoup(html.text, 'html.parser')

        # 1. img src url
        img_tag = soup.find('img', class_='film-poster-img')
        img_src = img_tag['src'] if img_tag else ""

        # 2. data-jname (Title)
        data_jname = soup.find('h2', class_='film-name')
        anime_title = data_jname['data-jname'] if data_jname and data_jname.has_attr("data-jname") else ""

        # 3. Tick items
        tick_pg = None
        tick_quality = None
        for tick_item in soup.select('.tick-item'):
            if 'tick-pg' in tick_item.get('class', []):
                tick_pg = tick_item.get_text(strip=True)
            if 'tick-quality' in tick_item.get('class', []):
                tick_quality = tick_item.get_text(strip=True)

        # 5. all item-title (all details + Studio)
        item_titles = {}
        for item in soup.select('.item.item-title, .item.item-list'):
            head = item.find('span', class_='item-head')
            if head:
                head_text = head.get_text(strip=True).replace(':', '')
                # For genres and producers, collect all <a> tags
                if 'Genre' in head_text:
                    values = [a.get_text(strip=True) for a in item.find_all('a')]
                    item_titles['Genres'] = ', '.join(values)
                    continue   # Skip rest: we handled this field
                if 'Producer' in head_text:
                    values = [a.get_text(strip=True) for a in item.find_all('a')]
                    item_titles['Producers'] = ', '.join(values)
                    continue   # Skip rest
                # Usual detail extraction
                values = []
                for tag in item.find_all(['span', 'a']):
                    if tag == head: continue
                    if 'item-head' in tag.get('class', []): continue
                    values.append(tag.get_text(strip=True))
                text_div = item.find('div', class_='text')
                if text_div:
                    values.append(text_div.get_text(strip=True).replace('\n', ' '))
                item_titles[head_text] = ', '.join([v for v in values if v])

        # JSON Structure
        output = {
            "img_src": img_src,
            "title": anime_title,
            "age": tick_pg,
            "quality": tick_quality,
            "details": item_titles,   
        }

        logger.info("Successfully extracted anime details for: %s", anime_title)
        return output
        
    except Exception as e:
        logger.error("Error getting anime details: %s", str(e), exc_info=True)
        return {}
    
    
    

