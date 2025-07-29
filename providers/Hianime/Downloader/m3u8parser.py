#/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# m3u8parser.py - This file contains the logic to parse M3U8 files and extract media streams.


from flask import Flask, Response, redirect
import requests
import m3u8
from config.hianime import proxy_headers, configure

# Your master/media playlist URL (local file or remote)
proxy_headers['Referer'] = "https://megacloud.club"
#playlist_path = requests.get("", headers=proxy_headers) # or an HTTP URL

app = Flask(__name__)

@app.route('/playlist.m3u8')
def playlist():
    # If reading from file:
    #with open(playlist_path, 'r') as f:
    #    playlist_text = f.read()
    # If from URL:
    playlist_text = requests.get("https://cdn.dotstream.buzz/anime/a9b4ec2eb4ab7b1b9c3392bb5388119d/c95bb2959d43dc119630bf216383b160/index-f2-v1-a1.m3u8", headers=proxy_headers).text

    # Rewrite segment URLs to point to our server
    new_lines = []
    for line in playlist_text.splitlines():
        if line.startswith("http"):
            # Remove extension for local proxying
            seg_id = line.split("/")[-1]
            newseg_url = f'/segment/{seg_id}'
            new_lines.append(newseg_url)
        else:
            new_lines.append(line)
    rewritten = "\n".join(new_lines)
    return Response(rewritten, mimetype='application/vnd.apple.mpegurl')

@app.route('/segment/<path:seg_id>')
def segment(seg_id):
    # Find the original full URL for this segment (must reconstruct or track map)
    base_url = 'https://cdn.dotstream.buzz/anime/a9b4ec2eb4ab7b1b9c3392bb5388119d/c95bb2959d43dc119630bf216383b160/index-f2-v1-a1.m3u8'
    url = f'{base_url}/{seg_id}'
    resp = requests.get(url, headers=proxy_headers, stream=True)
    # Always serve with correct content type for TS segments:
    return Response(resp.iter_content(chunk_size=1024), content_type='video/MP2T')
    
if __name__ == '__main__':
    # Visit http://localhost:5000/playlist.m3u8 in VLC/MPV etc.
    app.run(port=5000)


