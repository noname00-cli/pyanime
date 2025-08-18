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
from config.animekai import configure

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
        logger.debug("Making request to: %s/filter?keyword=%s", url, name)
        html = requests.get(f'{url}/filter?keyword={name}'.format(search=name), auth=('user', 'pass'), verify=False)
        logger.debug("Response status: %d", html.status_code)
        soup = BeautifulSoup(html.text, 'html.parser')
        items = soup.select('div.item')
        logger.info("Found %d anime blocks in search results", len(items))
        
        for idx, item in enumerate(items, 1):
        # Initialize variables
            No = idx
            title = None
            japanese_name = None
            type_ = None
            duration = None
            total_episodes = None
            sub_episodes = None
            dub_episodes = None
            watch_link = None
            image_url = None
            
            # Extract title and Japanese name
            title_link = item.select_one('.name.d-title')
            if title_link:
                title = title_link.text.strip()
                japanese_name = title_link.get('data-jp', '').strip()
                watch_link = title_link.get('href')
            
            # Extract image URL
            img = item.select_one('.poster img')
            if img:
                image_url = img.get('src')
            
            # Extract episode information from poster meta
            poster_meta = item.select_one('.poster .meta')
            if poster_meta:
                # Sub episodes
                sub_ep = poster_meta.select_one('.ep-status.sub span')
                if sub_ep:
                    sub_episodes = int(sub_ep.text.strip())
                
                # Dub episodes  
                dub_ep = poster_meta.select_one('.ep-status.dub span')
                if dub_ep:
                    dub_episodes = int(dub_ep.text.strip())
                
                # Total episodes
                total_ep = poster_meta.select_one('.ep-status.total span')
                if total_ep:
                    total_episodes = int(total_ep.text.strip())
                
                # Type
                type_info = poster_meta.select_one('.right')
                if type_info:
                    type_ = type_info.text.strip()
            
            # Build anime_details dictionary only with non-None values
            anime_details = {'No': No}
            
            if title:
                anime_details['Title'] = title
            if japanese_name:
                anime_details['Japanese Name'] = japanese_name
            if type_:
                anime_details['Type'] = type_
            if duration:
                anime_details['Duration'] = duration
            if total_episodes:
                anime_details['Episodes'] = total_episodes
            if sub_episodes:
                anime_details['Subs'] = sub_episodes
            if dub_episodes:
                anime_details['Dubs'] = dub_episodes
            
            # Add Imp section only if we have watch_link or image_url
            imp_data = {}
            if watch_link:
                imp_data['Watch Link'] = watch_link
            if image_url:
                imp_data['Image URL'] = image_url
            
            if imp_data:
                anime_details['Imp'] = imp_data

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
    
    try:
        logger.debug("Making request to: %s", watch_link)
        html = requests.get(watch_link, auth=('user', 'pass'), verify=False)
        logger.debug("Response status: %d", html.status_code)
        
        soup = BeautifulSoup(html.text, 'html.parser')
        # 1. Image source
        img_tag = soup.find('img', itemprop='image')
        img_src = img_tag['src'] if img_tag else ""
        
        # 2. Title (from h1 with class title d-title)
        data_jname = soup.find('h1', class_='title d-title')
        anime_title = data_jname.get_text(strip=True) if data_jname else ""
        
        # 3. Rating and Quality from meta icons
        tick_pg = None
        tick_quality = None
        meta_icons = soup.find('div', class_='meta icons')
        if meta_icons:
            for i_tag in meta_icons.find_all('i'):
                if 'rating' in i_tag.get('class', []):
                    tick_pg = i_tag.get_text(strip=True)
                if 'quality' in i_tag.get('class', []):
                    tick_quality = i_tag.get_text(strip=True)
        
        # 4. All item details from bmeta sections
        item_titles = {}
        
        # Synopsis
        synopsis_div = soup.find('div', class_='synopsis')
        if synopsis_div:
            content = synopsis_div.find('div', class_='content')
            if content:
                item_titles['Overview'] = content.get_text(strip=True)
        
        # Meta information from bmeta divs
        bmeta_divs = soup.find_all('div', class_='bmeta')
        for bmeta in bmeta_divs:
            meta_divs = bmeta.find_all('div', class_='meta')
            for meta_div in meta_divs:
                for item in meta_div.find_all('div', recursive=False):
                    text_content = item.get_text(strip=True)
                    if ':' in text_content:
                        parts = text_content.split(':', 1)
                        head_text = parts[0].strip()
                        
                        # For genres and producers, collect all <a> tags
                        if 'Genre' in head_text:
                            values = [a.get_text(strip=True) for a in item.find_all('a')]
                            item_titles['Genres'] = ', '.join(values)
                            continue
                        if 'Producer' in head_text:
                            values = [a.get_text(strip=True) for a in item.find_all('a')]
                            item_titles['Producers'] = ', '.join(values)
                            continue
                        if 'Studio' in head_text:
                            values = [a.get_text(strip=True) for a in item.find_all('a')]
                            item_titles['Studios'] = ', '.join(values)
                            continue
                        
                        # Regular details extraction
                        span_tag = item.find('span')
                        if span_tag:
                            # Check for links within span
                            links = span_tag.find_all('a')
                            if links:
                                values = [a.get_text(strip=True) for a in links]
                                item_titles[head_text] = ', '.join(values)
                            else:
                                item_titles[head_text] = span_tag.get_text(strip=True)
        
        # JSON Structure (matching your format exactly)
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
    
    
    

