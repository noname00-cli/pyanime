#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import requests
from bs4 import BeautifulSoup
from config.hianime import configure


def searchAnimeandetails(name):
    list_of_anime = []
    No = 0
    url = configure['baseurl']
    html = requests.get(f'{url}/search?keyword={name}'.format(search=name), auth=('user', 'pass'))
    soup = BeautifulSoup(html.text, 'html.parser')
    anime_blocks = soup.find_all('div', class_='flw-item')
    for block in anime_blocks:

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
            'No': No + 1,
            'Title': title,
            'Japanese Name': japanese_name,
            'Type': type_,
            'Duration': duration,
            'Sub Episodes Available': sub_episodes,
            'Dub Episodes Available': dub_episodes,
            'Total Episodes': total_episodes,
            'Image URL': image_url,
            'Watch Link': watch_link
        }

        list_of_anime.append(anime_details)
    return list_of_anime
    
    
print(searchAnimeandetails("Naruto"))  # Example usage

