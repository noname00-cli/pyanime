#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# getEpisodestreams.py - Extract episode streams from a given anime ID.

import sys
import os
import requests
from bs4 import BeautifulSoup
import re
import json

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from config.logging_config import get_logger, log_function_call, log_performance
from config.animekai import configure, proxy_headers, server_type

# Setup logging for this module
logger = get_logger("scraper.getEpisodestreams")


@log_function_call(logger)
@log_performance(logger)
def serverextractor(episode):
    logger.info("Extracting servers for episode: %s", episode["Title"])
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{episode['Watch Link']}",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0',
        'Accept-Encoding': 'gzip, deflate, br',
    }
    url = f"{configure['baseurl']}/ajax/server/list?servers={episode['Episode ID']}"
    url2 = f"https://mapper.kotostream.online/api/mal/{episode['MAL ID']}/1/{episode['Timestamp']}"
    
    logger.info("Fetching servers from URL: %s and %s", url, url2)
    
    try:
        # Make requests
        http = requests.get(url, headers=headers, verify=False, timeout=10)
        http2 = requests.get(url2, headers=headers, timeout=10)
        http.raise_for_status()
        http2.raise_for_status()
        
        # Parse responses
        hhh = http.text
        jsoni = json.loads(hhh)
        hh2 = http2.text
        s = json.loads(hh2)
        
        logger.debug("Successfully parsed JSON responses")
        
    except requests.exceptions.RequestException as e:
        logger.error("Network error while fetching servers for episode %s: %s", episode['Title'], str(e))
        return [], []
    except json.JSONDecodeError as e:
        logger.error("JSON decode error for episode %s: %s", episode['Title'], str(e))
        return [], []
    except KeyError as e:
        logger.error("Missing key in episode data: %s", str(e))
        return [], []
    except Exception as e:
        logger.error("Unexpected error extracting servers for episode %s: %s", episode['Title'], str(e))
        return [], []

    # Initialize containers
    hianime = {}
    animepahe = {"sub": [], "dub": []}
    
    # Process HiAnime servers
    try:
        if "result" not in jsoni:
            logger.warning("No 'result' key found in HiAnime response for episode %s", episode['Title'])
        else:
            hh = jsoni["result"]
            soup = BeautifulSoup(hh, 'html.parser')
            
            server_divs = soup.select("div.servers > div.type")
            if not server_divs:
                logger.warning("No server divs found in HTML for episode %s", episode['Title'])
            
            for server_type_div in server_divs:
                server_type = server_type_div.get("data-type")
                servers = []
                
                for li in server_type_div.select("ul > li"):
                    server = {
                        "name": li.get_text(strip=True),
                        "ep_id": li.get("data-ep-id"),
                        "link_id": li.get("data-link-id"),
                    }
                    servers.append(server)
                
                hianime[server_type] = servers
                logger.debug("Found %d %s servers for HiAnime", len(servers), server_type)
            
            total_hianime_servers = sum(len(servers) for servers in hianime.values())
            logger.info("Extracted %d HiAnime servers for episode %s", total_hianime_servers, episode['Title'])
            
    except Exception as e:
        logger.error("Error processing HiAnime servers for episode %s: %s", episode['Title'], str(e))

    # Process AnimePahe servers
    try:
        stream_keys = ['Kiwi-Stream-360p', 'Kiwi-Stream-720p', 'Kiwi-Stream-1080p']
        server_types = ['sub', 'dub']
        
        for stream_key in stream_keys:
            if stream_key not in s:
                logger.warning("Stream key %s not found in AnimePahe response for episode %s", stream_key, episode['Title'])
                continue
                
            for server_type in server_types:
                if server_type not in s[stream_key]:
                    logger.warning("Server type %s not found for %s in episode %s", server_type, stream_key, episode['Title'])
                    continue
                    
                if "url" not in s[stream_key][server_type]:
                    logger.warning("URL not found for %s %s in episode %s", stream_key, server_type, episode['Title'])
                    continue
                
                url_value = s[stream_key][server_type]["url"]
                animepahe[server_type].append({
                    "name": stream_key,
                    "ep_id": None,
                    "link_id": url_value
                })
        
        total_animepahe_servers = sum(len(servers) for servers in animepahe.values())
        logger.info("Extracted %d AnimePahe servers for episode %s", total_animepahe_servers, episode['Title'])
        
    except Exception as e:
        logger.error("Error processing AnimePahe servers for episode %s: %s", episode['Title'], str(e))

    # Final logging
    total_servers = (sum(len(servers) for servers in hianime.values()) + 
                    sum(len(servers) for servers in animepahe.values()))
    
    if total_servers == 0:
        logger.warning("No servers found for episode %s", episode['Title'])
    else:
        logger.info("Successfully extracted total %d servers for episode %s", total_servers, episode['Title'])
    
    return hianime, animepahe



@log_function_call(logger)
@log_performance(logger)
def streams(server, id_str):
    hd_1 = 'megaplay.buzz'
    hd_2 = 'vidwish.live'

    try:
        logger.info("Starting streams extraction for episode %s on server %s", id_str.get("Episode ID"), server.get("label"))

        proxy_headers["Referer"] = f"{configure['baseurl']}/watch/{id_str['URL']}"
        sources_resp = requests.get(f"{configure['baseurl']}/ajax/v2/episode/sources?id={server['data_id']}", headers=proxy_headers)
        sources_resp.raise_for_status()
        sources_data = sources_resp.json()
        logger.debug("Sources response status: %d", sources_resp.status_code)

        ajax_link = sources_data.get('link')
        if not ajax_link:
            logger.error("Missing link in sourcesData")
            raise Exception('Missing link in sourcesData')

        source_id_match = re.search(r'/([^/?]+)\?', ajax_link)
        source_id = source_id_match.group(1) if source_id_match else None
        if not source_id:
            raise Exception('Unable to extract sourceId from link')

        base_url_match = re.match(r'^(https?:\/\/[^/]+(?:\/[^/]+){3})', ajax_link)
        if not base_url_match:
            raise Exception('Could not extract base URL from ajaxLink')

        base_url = base_url_match.group(1)

        logger.debug("Extracted base URL: %s and source ID: %s", base_url, source_id)

        decrypted_sources = None
        raw_source_data = {}
        
        fallback = hd_1 if server['label'].lower() == server_type else hd_2
        proxy_headers["Referer"] = f"https://{fallback}/"
        if server['data_type'] == 'raw':
            root = f"https://{fallback}/stream/s-2/{id_str['Episode ID']}/sub"
        else:
            root = f"https://{fallback}/stream/s-2/{id_str['Episode ID']}/{server['data_type']}"
        html = requests.get(root, headers=proxy_headers).text
        data_id_match = re.search(r'data-id=["\'](\d+)["\']', html)
        real_id = data_id_match.group(1) if data_id_match else None
        if not real_id:
            raise Exception('Could not extract data-id')
        fallback_data = requests.get(
            f"https://{fallback}/stream/getSources?id={real_id}",
            headers={"X-Requested-With": "XMLHttpRequest", **configure['headers']})
        fallback_data.raise_for_status()
        fallback_data_json = fallback_data.json()
        decrypted_sources = [{"file": fallback_data_json['sources']['file']}]
        if not raw_source_data.get('tracks'):
            raw_source_data['tracks'] = fallback_data_json.get('tracks', [])
        if not raw_source_data.get('intro'):
            raw_source_data['intro'] = fallback_data_json.get('intro')
        if not raw_source_data.get('outro'):
            raw_source_data['outro'] = fallback_data_json.get('outro')

        logger.info("Extraction successful")
        return {
        "id": id_str,
        "server": server_type.upper(),
        "type": server["data_type"],
        "link": {
            "file": decrypted_sources[0]["file"] if decrypted_sources and decrypted_sources[0].get("file") else "",
            "type": "hls",
        },
        "tracks": raw_source_data.get("tracks", []),
        "intro": raw_source_data.get("intro"),
        "outro": raw_source_data.get("outro"),
    }

    except Exception as e:
        logger.error("Error during streams extraction for episode %s: %s", id_str, e, exc_info=True)
        return None
