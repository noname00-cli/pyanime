#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# getEpisodestreams.py - This file contains the logic to extract episode streams from a given anime ID.


import requests
import re
import json
from base64 import b64decode
from Crypto.Cipher import AES
from config.hianime import configure, proxy_headers, key


def serverextractor(selected_episodes):
    


def aes_cryptojs_decrypt(ciphertext_b64, key):
    ct = b64decode(ciphertext_b64)
    iv = bytes([0] * 16)
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(ct)
    pad_len = decrypted[-1]
    decrypted = decrypted[:-pad_len]
    return decrypted.decode('utf-8')


def megacloud(server, id_str):
    fallback_1 = 'megaplay.buzz'
    fallback_2 = 'vidwish.live'

    try:
        proxy_headers["Referer"] = f"{configure['baseurl']}/watch/{id_str["URL"]}"
        sources_resp = requests.get(f"{configure['baseurl']}/ajax/v2/episode/sources?id={server['Episodo ID']}",headers=proxy_headers)
        key_resp = requests.get(key)
        sources_data = sources_resp.json()
        keys = key_resp.text.strip()
        ajax_link = sources_data.get('link')
        if not ajax_link:
            raise Exception('Missing link in sourcesData')
        source_id_match = re.search(r'/([^/?]+)\?', ajax_link)
        source_id = source_id_match.group(1) if source_id_match else None
        if not source_id:
            raise Exception('Unable to extract sourceId from link')
        base_url_match = re.match(r'^(https?:\/\/[^/]+(?:\/[^/]+){3})', ajax_link)
        if not base_url_match:
            raise Exception('Could not extract base URL from ajaxLink')
        base_url = base_url_match.group(1)
        decrypted_sources = None
        raw_source_data = {}
        try:
            token = extract_token(f"{base_url}/{source_id}?k=1&autoPlay=0&oa=0&asi=1")
            resp = requests.get(f"{base_url}/getSources?id={source_id}&_k={token}", headers=proxy_headers)
            raw_source_data = resp.json()
            encrypted = raw_source_data.get('sources')
            if not encrypted:
                raise Exception('Encrypted source missing')
            decrypted = aes_cryptojs_decrypt(encrypted, keys)
            if not decrypted:
                raise Exception('Failed to decrypt source')
            decrypted_sources = json.loads(decrypted)
        except Exception as main_err:
            try:
                fallback = fallback_1 if server['name'].lower() == 'hd-1' else fallback_2
                proxy_headers["Referer"] = f"https://{fallback_1}/"
                html = requests.get(f"https://{fallback}/stream/s-2/{id_str["Episode ID"]}/{server["type"]}", headers=proxy_headers).text
                data_id_match = re.search(r'data-id=["\'](\d+)["\']', html)
                real_id = data_id_match.group(1) if data_id_match else None
                if not real_id:
                    raise Exception('Could not extract data-id for fallback')
                fallback_data = requests.get(
                    f"https://{fallback}/stream/getSources?id={real_id}",
                    headers={"X-Requested-With": "XMLHttpRequest", **configure['headers']}).json()
                decrypted_sources = [{"file": fallback_data['sources']['file']}]
                if not raw_source_data.get('tracks'):
                    raw_source_data['tracks'] = fallback_data.get('tracks', [])
                if not raw_source_data.get('intro'):
                    raw_source_data['intro'] = fallback_data.get('intro')
                if not raw_source_data.get('outro'):
                    raw_source_data['outro'] = fallback_data.get('outro')
            except Exception as e:
                raise Exception(f"Fallback failed: {e}")
        return {
                "id": id_str,
                "type": server["type"],
                "link": {
                    "file": decrypted_sources[0]["file"] if decrypted_sources and decrypted_sources[0].get("file") else "",
                    "type": "hls",
                },
                "tracks": raw_source_data.get("tracks", []),
                "intro": raw_source_data.get("intro"),
                "outro": raw_source_data.get("outro"),
                "server": server["name"],
            }
    except Exception as e:
        print(f"Error during megacloud({id_str}): {e}")
        return None