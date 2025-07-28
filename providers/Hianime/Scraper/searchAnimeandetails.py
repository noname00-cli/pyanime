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
    junk = soup.find_all(class_='flw-item')
    for recycled_junk in junk:
        anime_name = recycled_junk.find('h3', class_='film-name').find('a')['title']
        anime_jname = recycled_junk.find('h3', class_='film-name').find('a').get('data-jname', '')
        type_span = recycled_junk.find('span', class_='fdi-item')
        type = type_span.text.strip() if type_span else ''
        duration_span = recycled_junk.find('span', class_='fdi-duration')
        duration = duration_span.text.strip() if duration_span else ''
        cc_div = recycled_junk.find('div', class_='tick-item tick-sub')
        closed_caption_count = cc_div.text.strip() if cc_div else ''
        img = recycled_junk.find('img', class_='film-poster-img')
        image_url = img['data-src'] if img else ''
        watch_link = ''
        watch_a = recycled_junk.find('a', class_='film-poster-ahref')
        if watch_a:
            watch_link = watch_a['href']
        No += 1

        # Appending the details to the list
        list_of_anime.append({
            'Sl-no' : No,
            'Name' : anime_name,
            'Japanese Name' : anime_jname,
            'Type' : type,
            'Duration' : duration,
            'Closed Caption Count' : closed_caption_count,
            'Image URL' : image_url,
            'URL' : watch_link,
        })
        return list_of_anime

