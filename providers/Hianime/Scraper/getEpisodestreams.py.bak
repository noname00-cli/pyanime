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
from base64 import b64decode
from Crypto.Cipher import AES

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from config.logging_config import get_logger, log_function_call, log_performance
from config.hianime import configure, proxy_headers, key, server_type
from providers.Hianime.Scraper.tokenextractor import extract_token

# Setup logging for this module
logger = get_logger("scraper.getEpisodestreams")


@log_function_call(logger)
@log_performance(logger)
def serverextractor(episode):
    logger.info("Extracting servers for episode: %s", episode.get('Episode ID', 'Unknown'))
    class_lists = [['ps_-block-sub', 'servers-sub'], ['ps_-block-sub', 'servers-dub']]
    url = f"{configure['baseurl']}/ajax/v2/episode/servers?episodeId={episode['Episode ID']}"
    proxy_headers["Referer"] = f"{configure['baseurl']}{episode['URL']}"
    logger.info("Fetching servers from URL: %s", url)
    try:
        http = requests.get(url, headers=proxy_headers)
        http.raise_for_status()
        data = http.json()
        logger.debug("Server response status: %d", http.status_code)
    except Exception as e:
        logger.error("Failed to get servers for episode %s: %s", episode['Episode ID'], e, exc_info=True)
        return []

    if 'html' not in data:
        logger.error("No 'html' key in response data for episode %s", episode['Episode ID'])
        return []

    html_content = data['html']
    dust = BeautifulSoup(html_content, 'html.parser')
    servers = []

    for class_list in class_lists:
        selector = 'div.' + '.'.join(class_list)
        block = dust.select_one(selector)
        if block:
            items = block.find_all('div', class_='item')
            logger.info("Found %d server items for class %s", len(items), class_list)
            for item in items:
                data_id = item.get('data-id')
                data_server_id = item.get('data-server-id')
                data_type = item.get('data-type')
                label = None
                a_tag = item.find('a', class_='btn')
                if a_tag:
                    label = a_tag.text.strip()
                servers.append({
                    "data_id": data_id,
                    "data_server_id": data_server_id,
                    "data_type": data_type,
                    "label": label
                })
        else:
            logger.warning("There is NO %s for this Episode %s", class_list[1][8:], episode['Episode ID'])

    logger.info("Extracted %d servers total for episode %s", len(servers), episode['Episode ID'])
    return servers

@log_function_call(logger)
def aes_cryptojs_decrypt(ciphertext_b64, key):
    logger.debug("Attempting AES decryption")
    try:
        ct = b64decode(ciphertext_b64)
        iv = bytes([0] * 16)
        cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(ct)
        pad_len = decrypted[-1]
        decrypted = decrypted[:-pad_len]
        result = decrypted.decode('utf-8')
        logger.debug("Decryption successful")
        return result
    except Exception as e:
        logger.error("AES decryption error: %s", e, exc_info=True)
        raise

@log_function_call(logger)
@log_performance(logger)
def streams(server, id_str):
    fallback_1 = 'megaplay.buzz'
    fallback_2 = 'vidwish.live'

    try:
        logger.info("Starting streams extraction for episode %s on server %s", id_str.get("Episode ID"), server.get("label"))

        proxy_headers["Referer"] = f"{configure['baseurl']}/watch/{id_str['URL']}"
        sources_resp = requests.get(f"{configure['baseurl']}/ajax/v2/episode/sources?id={server['data_id']}", headers=proxy_headers)
        sources_resp.raise_for_status()
        sources_data = sources_resp.json()
        logger.debug("Sources response status: %d", sources_resp.status_code)

        key_resp = requests.get(key)
        key_resp.raise_for_status()
        keys = key_resp.text.strip()
        logger.debug("Retrieved encryption keys")

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

        try:
            token = extract_token(f"{base_url}/{source_id}?k=1&autoPlay=0&oa=0&asi=1")
            resp = requests.get(f"{base_url}/getSources?id={source_id}&_k={token}", headers=proxy_headers)
            resp.raise_for_status()
            raw_source_data = resp.json()
            encrypted = raw_source_data.get('sources')
            if not encrypted:
                raise Exception('Encrypted source missing')
            decrypted = aes_cryptojs_decrypt(encrypted, keys)
            if not decrypted:
                raise Exception('Failed to decrypt source')
            decrypted_sources = json.loads(decrypted)
            logger.info("Decrypted and loaded sources successfully")
        except Exception as main_err:
            logger.warning("Main source extraction failed: %s, attempting fallback...", main_err)
            try:
                fallback = fallback_1 if server['label'].lower() == server_type else fallback_2
                proxy_headers["Referer"] = f"https://{fallback}/"
                root = f"https://{fallback}/stream/s-2/{id_str['Episode ID']}/{server['data_type']}"
                html = requests.get(root, headers=proxy_headers).text
                data_id_match = re.search(r'data-id=["\'](\d+)["\']', html)
                real_id = data_id_match.group(1) if data_id_match else None
                if not real_id:
                    raise Exception('Could not extract data-id for fallback')
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

                logger.info("Fallback extraction successful")
            except Exception as e:
                logger.error("Fallback failed during streams extraction: %s", e, exc_info=True)
                raise Exception(f"Fallback failed: {e}")

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
