#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# m3u8parser.py - This file contains the logic to parse M3U8 files and extract media streams.

import asyncio
import aiohttp
import aiofiles
import ffmpeg
import requests
import os
import m3u8
import time
import tempfile
import shutil
import random
import sys
from urllib.parse import urljoin
from config.hianime import quality, parallel, logger, timeout, proxy_servers

hd2_headers = {
    'user-agent': "Mozilla/5.0 (X11; Linux aarch64; rv:122.0) Gecko/20100101 Firefox/122.0",
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.5',
    'origin': 'https://vidwish.live',
    'referer': 'https://vidwish.live/',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'te': 'trailers',
}

hd1_headers = {
    'user-agent': "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.5',
    'origin': 'https://megaplay.buzz',
    'referer': 'https://megaplay.buzz/',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'te': 'trailers',
}

def proxy(url, headers, proxy_servers, timeout):
    """Try to fetch URL with native IP, then try with proxies if that fails"""
    try:
        logger.debug("Trying native IP for %s", url)
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            logger.debug("Native IP request successful")
            return response
        
        logger.warning("Native IP request failed with status %s, trying proxies", response.status_code)
        for proxy_server in proxy_servers:
            try:
                logger.debug("Trying proxy %s for %s", proxy_server, url)
                proxies = {
                    'http': proxy_server,
                    'https': proxy_server
                }
                response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)
                if response.status_code == 200:
                    logger.debug("Proxy request successful with %s", proxy_server)
                    return response
                logger.warning("Proxy %s request failed with status %s", proxy_server, response.status_code)
            except Exception as e:
                logger.error("Error with proxy %s: %s", proxy_server, e)
                continue
        
        logger.error("All proxy attempts failed for %s", url)
        return None
    except Exception as e:
        logger.error("Error in proxy function: %s", e)
        return None

def m3u8_parsing(m3u8_dict):
    try:
        logger.info("Starting m3u8_parsing for: %s", m3u8_dict.get("id", {}).get("Title", "Unknown"))
        url = m3u8_dict["link"]["file"]
        subtitles = m3u8_dict["tracks"]
        intro = m3u8_dict["intro"]
        outro = m3u8_dict["outro"]
        logger.debug("URL: %s | Subtitles: %s | Intro: %s | Outro: %s", url, subtitles, intro, outro)
        m3u8_data = proxy(url, hd2_headers, proxy_servers, timeout)
        if not m3u8_data or m3u8_data.status_code != 200:
            logger.error("Failed to fetch m3u8 data: %s", url)
            return None, m3u8_dict["id"]["Title"], subtitles
            
        logger.info("Requested m3u8: %s | Status: %s", url, m3u8_data.status_code)
        playlist_str = m3u8_data.text
        m3u8_obj = m3u8.loads(playlist_str)
        Name = m3u8_dict["id"]["Title"]
        
        # If no playlists found, this might be a direct media playlist
        if not m3u8_obj.playlists:
            logger.info("No variant playlists found, using direct media playlist")
            return playlist_str, Name, subtitles
            
        # Try to find the requested quality
        for playlist in m3u8_obj.playlists:
            if not hasattr(playlist.stream_info, 'resolution') or not playlist.stream_info.resolution:
                continue
                
            stream_quality = f"{playlist.stream_info.resolution}".strip("()").replace(" ", "").split(",")[1]+"p"
            logger.debug("Checking stream quality: %s vs target: %s", stream_quality, quality)
            if quality == stream_quality:
                final_url = m3u8_dict["link"]["file"].replace('/master.m3u8', f'/{playlist.uri}')
                final_media = proxy(final_url, hd2_headers, proxy_servers, timeout)
                if not final_media or final_media.status_code != 200:
                    logger.error("Failed to fetch final media: %s", final_url)
                    continue
                    
                logger.info("Fetched final media: %s | Status: %s", final_url, final_media.status_code)
                return final_media.text, Name, subtitles
                
        # If requested quality not found, use the highest available quality
        logger.warning("Requested quality %s not found, using highest available", quality)
        highest_resolution = 0
        highest_playlist = None
        
        for playlist in m3u8_obj.playlists:
            if not hasattr(playlist.stream_info, 'resolution') or not playlist.stream_info.resolution:
                continue
                
            resolution = playlist.stream_info.resolution
            if resolution and len(resolution) >= 2:
                height = int(resolution[1])
                if height > highest_resolution:
                    highest_resolution = height
                    highest_playlist = playlist
        
        if highest_playlist:
            final_url = m3u8_dict["link"]["file"].replace('/master.m3u8', f'/{highest_playlist.uri}')
            final_media = proxy(final_url, hd2_headers, proxy_servers, timeout)
            if final_media and final_media.status_code == 200:
                logger.info("Using highest quality: %dp", highest_resolution)
                return final_media.text, Name, subtitles
        
        return None, Name, subtitles
    except Exception as e:
        logger.error("Exception in m3u8_parsing: %s", e, exc_info=True)
        return None, None, None

# Async functions for parallel downloading
async def _download_segment(session, semaphore, segment_url, segment_index, temp_dir, progress_queue=None):
    """Download a single segment asynchronously with unlimited retries"""
    async with semaphore:
        retry_count = 0
        backoff_time = 1  # Start with 1 second backoff, will increase with exponential backoff
        max_backoff = 30  # Maximum backoff time in seconds
        
        while True:  # Unlimited retries
            try:
                # Log the segment URL being downloaded for debugging
                logger.debug("Downloading segment %d from URL: %s (attempt %d)", 
                           segment_index, segment_url, retry_count + 1)
                
                # Add timeout for individual segment download
                async with session.get(segment_url, headers=hd2_headers, timeout=timeout) as response:
                    if response.status != 200:
                        logger.warning("Segment %d returned status code %d (attempt %d)", 
                                     segment_index, response.status, retry_count + 1)
                        retry_count += 1
                        # Use exponential backoff with jitter
                        backoff_time = min(backoff_time * 1.5, max_backoff) * (0.8 + 0.4 * random.random())
                        await asyncio.sleep(backoff_time)  # Wait before retry
                        continue
                    
                    segment_file = os.path.join(temp_dir, f"segment_{segment_index:06d}.ts")
                    
                    # Check if response has content
                    content_length = response.headers.get('Content-Length')
                    if content_length and int(content_length) == 0:
                        logger.warning("Segment %d has zero content length (attempt %d)", 
                                     segment_index, retry_count + 1)
                        retry_count += 1
                        await asyncio.sleep(backoff_time)  # Wait before retry
                        continue
                    
                    # Write segment data to file
                    async with aiofiles.open(segment_file, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    
                    # Verify file was created and has content
                    if os.path.exists(segment_file) and os.path.getsize(segment_file) > 0:
                        logger.debug("Successfully downloaded segment %d", segment_index + 1)
                        # Update progress if queue is provided
                        if progress_queue is not None:
                            await progress_queue.put(("success", segment_index))
                        return segment_file, segment_index
                    else:
                        logger.warning("Segment %d file is empty or not created (attempt %d)", 
                                     segment_index, retry_count + 1)
                        retry_count += 1
                        await asyncio.sleep(backoff_time)  # Wait before retry
                        continue
                    
            except asyncio.TimeoutError:
                logger.warning("Timeout downloading segment %d (attempt %d)", 
                              segment_index, retry_count + 1)
                retry_count += 1
                # Update progress if queue is provided
                if progress_queue is not None:
                    await progress_queue.put(("retry", segment_index))
                await asyncio.sleep(backoff_time)  # Wait before retry
            except Exception as e:
                logger.error("Error downloading segment %d: %s (attempt %d)", 
                            segment_index, e, retry_count + 1)
                retry_count += 1
                # Update progress if queue is provided
                if progress_queue is not None:
                    await progress_queue.put(("retry", segment_index))
                await asyncio.sleep(backoff_time)  # Wait before retry

async def _update_progress_bar(progress_queue, total_segments):
    """Display and update a progress bar for segment downloads"""
    completed = 0
    retries = 0
    terminal_width = shutil.get_terminal_size().columns
    bar_width = min(terminal_width - 50, 50)  # Ensure bar fits in terminal
    
    while completed < total_segments:
        try:
            status, segment_index = await asyncio.wait_for(progress_queue.get(), timeout=0.5)
            
            if status == "success":
                completed += 1
            elif status == "retry":
                retries += 1
                
            # Calculate progress percentage
            percent = completed / total_segments
            filled_length = int(bar_width * percent)
            
            # Create the progress bar
            bar = '█' * filled_length + '░' * (bar_width - filled_length)
            
            # Print progress bar with stats
            sys.stdout.write(f"\r[{bar}] {completed}/{total_segments} segments | {int(percent*100)}% | Retries: {retries}")
            sys.stdout.flush()
            
        except asyncio.TimeoutError:
            # Just update the display without changing counts
            if completed > 0:
                percent = completed / total_segments
                filled_length = int(bar_width * percent)
                bar = '█' * filled_length + '░' * (bar_width - filled_length)
                sys.stdout.write(f"\r[{bar}] {completed}/{total_segments} segments | {int(percent*100)}% | Retries: {retries}")
                sys.stdout.flush()
    
    # Final update to show 100% completion
    bar = '█' * bar_width
    sys.stdout.write(f"\r[{bar}] {total_segments}/{total_segments} segments | 100% | Retries: {retries}\n")
    sys.stdout.flush()
    logger.info(f"Downloaded {total_segments} segments with {retries} retries")

async def _download_all_segments(m3u8_url, segments, temp_dir, max_concurrent):
    """Download all segments concurrently with improved error handling and progress bar"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # Ensure base_url ends with a slash for proper joining
    if m3u8_url and not m3u8_url.endswith('/'):
        base_url = m3u8_url + '/'
    else:
        base_url = m3u8_url or ''
    
    # Log the base URL for debugging
    logger.info("Using base URL for segments: %s", base_url)
    
    # Configure connection pooling and timeouts
    connector = aiohttp.TCPConnector(limit=max_concurrent * 2, force_close=False)
    timeout_config = aiohttp.ClientTimeout(total=timeout * 2)  # Double the timeout for the session
    
    # Create progress queue for tracking download progress
    progress_queue = asyncio.Queue()
    
    async with aiohttp.ClientSession(
        connector=connector, 
        timeout=timeout_config,
        headers=hd2_headers
    ) as session:
        tasks = []
        valid_segments = 0
        
        for i, segment in enumerate(segments):
            try:
                # Extract segment URI based on type
                if hasattr(segment, 'uri'):
                    segment_url = segment.uri  # m3u8.Segment object
                elif isinstance(segment, dict) and 'uri' in segment:
                    segment_url = segment['uri']
                else:
                    logger.warning("Segment %d has invalid format: %s", i, segment)
                    continue
                
                # Skip empty URIs
                if not segment_url or segment_url.strip() == '':
                    logger.warning("Segment %d has empty URI", i)
                    continue
                
                # Handle relative URLs
                if not segment_url.startswith('http'):
                    segment_url = urljoin(base_url, segment_url)
                
                # Validate URL format
                if not segment_url.startswith('http'):
                    logger.warning("Segment %d has invalid URL: %s", i, segment_url)
                    continue
                
                # Create download task with progress queue
                task = _download_segment(session, semaphore, segment_url, i, temp_dir, progress_queue)
                tasks.append(task)
                valid_segments += 1
            except Exception as e:
                logger.error("Error processing segment %d: %s", i, e)
        
        logger.info("Created %d download tasks out of %d segments", valid_segments, len(segments))
        
        if not tasks:
            logger.error("No valid segments to download")
            return []
        
        # Start progress bar task
        progress_task = asyncio.create_task(_update_progress_bar(progress_queue, valid_segments))
        
        # Execute all download tasks
        print(f"Downloading {valid_segments} segments with {max_concurrent} concurrent connections...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Wait for progress bar to complete
        try:
            await progress_task
        except Exception as e:
            logger.error("Error in progress bar: %s", e)
    
    # Process results
    successful = []
    failed = 0
    
    for result in results:
        if isinstance(result, Exception):
            logger.error("Task exception: %s", result)
            failed += 1
        elif result[0] is None:
            failed += 1
        else:
            successful.append(result)
    
    logger.info("Downloaded %d/%d segments successfully", len(successful), len(tasks))
    
    # Sort segments by index to maintain proper order
    successful.sort(key=lambda x: x[1])
    return [seg_file for seg_file, _ in successful]

async def download_subtitles(subtitles, temp_dir):
    """Download subtitles asynchronously"""
    downloaded_subs = []
    
    # Filter out thumbnails and only get captions/subtitles
    subtitle_tracks = [
        sub for sub in subtitles 
        if sub.get('kind') in ['subtitles', 'captions'] and sub.get('kind') != 'thumbnails'
    ]
    
    if not subtitle_tracks:
        logger.info("No subtitle tracks found to download")
        return []
    
    try:
        connector = aiohttp.TCPConnector(limit=10)
        timeout_config = aiohttp.ClientTimeout(total=timeout)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout_config,
            headers=hd2_headers
        ) as session:
            
            tasks = []
            for i, sub in enumerate(subtitle_tracks):
                subtitle_url = sub['file']
                label = sub['label']
                
                # Create safe filename
                safe_label = ''.join(ch for ch in label if ch.isalnum() or ch in '-_ ')
                subtitle_filename = f"{safe_label}_{i}.vtt"
                subtitle_path = os.path.join(temp_dir, subtitle_filename)
                
                # Create download task
                task = download_single_subtitle(session, subtitle_url, subtitle_path, label)
                tasks.append((task, sub, subtitle_path))
            
            # Wait for all downloads
            for task, sub_info, subtitle_path in tasks:
                try:
                    result = await task
                    if result:
                        downloaded_subs.append({
                            'path': subtitle_path,
                            'label': sub_info['label'],
                        })
                        logger.info("Downloaded subtitle: %s", sub_info['label'])
                except Exception as e:
                    logger.error("Failed to download subtitle %s: %s", sub_info['label'], e)
                    
    except Exception as e:
        logger.error("Error in download_subtitles: %s", e)
    
    logger.info("Downloaded %d subtitle files", len(downloaded_subs))
    return downloaded_subs

async def download_single_subtitle(session, subtitle_url, subtitle_path, label):
    """Download a single subtitle file"""
    try:
        async with session.get(subtitle_url, headers=hd2_headers) as response:
            response.raise_for_status()
            content = await response.text()
            
            async with aiofiles.open(subtitle_path, 'w', encoding='utf-8') as f:
                await f.write(content)
                
            return True
    except Exception as e:
        logger.error("Error downloading subtitle %s: %s", label, e)
        return False


def _concatenate_segments(segment_files, temp_dir):
    """Concatenate TS segments using ffmpeg with improved error handling"""
    # Check if we have any segments to concatenate
    if not segment_files:
        logger.error("No segment files to concatenate")
        raise ValueError("No segment files to concatenate")
    
    logger.info("Preparing to concatenate %d segment files", len(segment_files))
    
    # Verify all segment files exist and have content
    valid_segments = []
    for segment_file in segment_files:
        if os.path.exists(segment_file) and os.path.getsize(segment_file) > 0:
            valid_segments.append(segment_file)
        else:
            logger.warning("Skipping missing or empty segment file: %s", segment_file)
    
    if not valid_segments:
        logger.error("No valid segment files to concatenate")
        raise ValueError("No valid segment files to concatenate")
    
    logger.info("Found %d valid segment files out of %d total", len(valid_segments), len(segment_files))
    
    # Create concat file list
    concat_file = os.path.join(temp_dir, "file_list.txt")
    
    with open(concat_file, 'w') as f:
        for segment_file in valid_segments:
            # Escape single quotes in file paths
            escaped_path = segment_file.replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")
    
    temp_output = os.path.join(temp_dir, "concatenated.ts")
    
    try:
        logger.debug("Running ffmpeg to concatenate segments")
        (
            ffmpeg
            .input(concat_file, format='concat', safe=0)
            .output(temp_output, c='copy')
            .run(overwrite_output=True, quiet=True)
        )
        
        # Verify the output file was created and has content
        if os.path.exists(temp_output) and os.path.getsize(temp_output) > 0:
            logger.info("Successfully concatenated segments to: %s", temp_output)
            return temp_output
        else:
            logger.error("Concatenated file is empty or not created: %s", temp_output)
            raise ValueError("Concatenated file is empty or not created")
    except Exception as e:
        logger.error("Error concatenating segments: %s", e)
        raise

def _mux_with_subtitles(video_file, output_file, downloaded_subs=None):
    """Mux video with subtitles"""
    try:
        # Validate video file
        if not video_file or not os.path.exists(video_file):
            logger.error("Video file does not exist: %s", video_file)
            raise ValueError(f"Video file does not exist: {video_file}")
        
        # Handle case with no subtitles
        if not downloaded_subs:
            logger.info("Muxing video without subtitles")
            (
                ffmpeg
                .input(video_file)
                .output(output_file, c='copy')
                .run(overwrite_output=True, quiet=True)
            )
            return
        
        # Process subtitle files - handle both string paths and dictionary objects
        subtitle_paths = []
        for sub in downloaded_subs:
            if isinstance(sub, dict) and 'path' in sub:
                # Extract path from dictionary
                sub_path = sub['path']
                if os.path.exists(sub_path):
                    subtitle_paths.append(sub_path)
                    logger.debug("Adding subtitle: %s", sub.get('label', 'Unknown'))
                else:
                    logger.warning("Subtitle file not found: %s", sub_path)
            elif isinstance(sub, str) and os.path.exists(sub):
                # Direct path string
                subtitle_paths.append(sub)
                logger.debug("Adding subtitle file: %s", sub)
            else:
                logger.warning("Invalid subtitle specification: %s", sub)
        
        # If no valid subtitle paths were found, just mux the video
        if not subtitle_paths:
            logger.info("No valid subtitle files found, muxing video only")
            (
                ffmpeg
                .input(video_file)
                .output(output_file, c='copy')
                .run(overwrite_output=True, quiet=True)
            )
            return
        
        # Create inputs for ffmpeg
        logger.info("Muxing video with %d subtitle tracks", len(subtitle_paths))
        inputs = [ffmpeg.input(video_file)]
        inputs.extend([ffmpeg.input(sub_path) for sub_path in subtitle_paths])
        
        # Set up output parameters
        output_kwargs = {'c:v': 'copy', 'c:a': 'copy', 'avoid_negative_ts': 'disabled'}
        
        for i in range(len(subtitle_paths)):
            output_kwargs[f'c:s:{i}'] = 'copy'
            

        
        # Run ffmpeg
        (
            ffmpeg
            .output(*inputs, output_file, **output_kwargs)
            .run(overwrite_output=True, quiet=True)
        )
        
        # Verify output file was created
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            logger.info("Successfully muxed video with subtitles to: %s", output_file)
        else:
            logger.error("Muxing failed or produced empty file: %s", output_file)
            raise ValueError(f"Muxing failed or produced empty file: {output_file}")
            
    except Exception as e:
        logger.error("Error muxing with subtitles: %s", e)
        raise

def _print_progress_step(step, total_steps, message):
    """Log a progress step without displaying a progress bar"""
    # Log the progress step instead of displaying a progress bar
    logger.info(f"Step {step}/{total_steps}: {message}")

async def downloading(segments, Name, Anime, subtitles=None, base_url=None):
    """
    Download m3u8 segments with parallel downloads and subtitle muxing
    
    Args:
        segments (str): M3U8 playlist content as string
        Name (str): Episode/video name
        Anime (str): Anime/series name
        subtitle_files (list, optional): List of subtitle file paths
        base_url (str, optional): Base URL for resolving relative paths in m3u8
    
    Returns:
        int: 0 for success, 1 for failure
    """
    temp_dir = None
    try:
        # Define total steps for progress tracking
        total_steps = 4  # Parse, Download, Concatenate, Mux
        current_step = 0
        
        logger.info("Starting download for %s in %s", Name, Anime)
        
        # Step 1: Parse and prepare
        current_step += 1
        _print_progress_step(current_step, total_steps, "Preparing download")
        
        # Clean filename characters
        chars_to_remove = set(r'\\/"?*|')
        fixed_Name = ''.join(ch for ch in Name if ch not in chars_to_remove)
        fixed_Anime = ''.join(ch for ch in Anime if ch not in chars_to_remove)
        
        # Setup directories
        home_dir = os.path.expanduser("~")
        cache = f"{home_dir}/.animecache/{fixed_Anime}"
        os.makedirs(cache, exist_ok=True)
        logger.debug("Cache directory created at %s", cache)
        
        # Check if file already exists
        output_file = os.path.join(cache, f"{fixed_Name}.mkv")
        if os.path.exists(output_file):
            logger.info("File already exists: %s", output_file)
            return 0
        
        temp_dir = tempfile.mkdtemp()
        logger.debug("Created temporary directory: %s", temp_dir)
        
        # Validate m3u8 content
        if not segments or not isinstance(segments, str) or len(segments.strip()) == 0:
            logger.error("Invalid or empty m3u8 content")
            return 1
        
        # Parse m3u8 segments
        logger.info("Parsing m3u8 segments...")
        try:
            playlist = m3u8.loads(segments)
            segments_list = playlist.segments
        except Exception as e:
            logger.error("Failed to parse m3u8 content: %s", e)
            return 1
        
        if not segments_list:
            logger.error("No segments found in m3u8 playlist")
            return 1
        
        logger.info("Found %d segments", len(segments_list))
        
        # Extract base URL from the first segment if available and not provided
        if not base_url:
            # Try to extract base URL from the first segment if it has an absolute URL
            first_segment = segments_list[0]
            if hasattr(first_segment, 'uri') and first_segment.uri.startswith('http'):
                base_url = '/'.join(first_segment.uri.split('/')[:-1]) + '/'
                logger.info("Extracted base URL from segment: %s", base_url)
            else:
                # Try to extract from the m3u8 URI if available
                if hasattr(playlist, 'uri') and playlist.uri and playlist.uri.startswith('http'):
                    base_url = '/'.join(playlist.uri.split('/')[:-1]) + '/'
                    logger.info("Extracted base URL from playlist URI: %s", base_url)
                else:
                    # Default fallback base URL - this should be extracted from the m3u8 URL
                    logger.warning("Could not determine base URL from segments or playlist")
                    return 1
        
        # Step 2: Download segments
        current_step += 1
        _print_progress_step(current_step, total_steps, "Downloading segments")
        logger.info("Starting async download with %d concurrent downloads...", parallel)
        segment_files = await _download_all_segments(base_url, segments_list, temp_dir, parallel)
        
        if not segment_files:
            logger.error("No segments downloaded successfully")
            return 1
        
        # Check if we have enough segments to make a valid video
        min_segments_required = max(5, int(len(segments_list) * 0.1))  # At least 5 segments or 10% of total
        if len(segment_files) < min_segments_required:
            logger.error("Too few segments downloaded (%d/%d). Need at least %d segments for a valid video.", 
                         len(segment_files), len(segments_list), min_segments_required)
            return 1
        
        # Step 3: Concatenate
        current_step += 1
        _print_progress_step(current_step, total_steps, "Concatenating segments")
        logger.info("Concatenating segments...")
        try:
            concatenated_file = _concatenate_segments(segment_files, temp_dir)
            if not concatenated_file or not os.path.exists(concatenated_file) or os.path.getsize(concatenated_file) == 0:
                logger.error("Concatenation failed or produced empty file")
                return 1
        except Exception as e:
            logger.error("Error concatenating segments: %s", e)
            return 1
        
        # Step 4: Mux with subtitles
        current_step += 1
        _print_progress_step(current_step, total_steps, "Muxing final output")
        logger.info("Muxing final output...")
        try:
            downloaded_subtitles = []
            if subtitles:
                # Download subtitles asynchronously
                downloaded_subtitles = await download_subtitles(subtitles, temp_dir)
                if not downloaded_subtitles:
                    logger.warning("No subtitles downloaded, proceeding without subtitles")
            _mux_with_subtitles(concatenated_file, output_file, downloaded_subtitles)
            if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                logger.error("Muxing failed or produced empty file")
                return 1
        except Exception as e:
            logger.error("Error muxing with subtitles: %s", e)
            return 1
        
        # Display a spinner after download completion
        print("Adding Subtitles", end="")
        spinner_chars = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
        for _ in range(20):  # Show spinner for a short time
            for char in spinner_chars:
                sys.stdout.write(f"\r{char} Processing file...")
                sys.stdout.flush()
                await asyncio.sleep(0.1)
        sys.stdout.write("\r✓ Adding completed👌!     \n")
        sys.stdout.flush()
        
        return 0
        
    except Exception as e:
        logger.error("Exception in downloading function: %s", e, exc_info=True)
        return 1
    finally:
        # Always clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.debug("Cleaned up temporary directory: %s", temp_dir)
            except Exception as e:
                logger.warning("Failed to clean up temporary directory: %s", e)

# Keep the original synchronous version as fallback
def downloading_sync(segments, Name, Anime):
    """Original synchronous downloading function using yt-dlp"""
    try:
        logger.info("Starting download for %s in %s", Name, Anime)
        chars_to_remove = set(r'\/"?*|')
        fixed_Name = ''.join(ch for ch in Name if ch not in chars_to_remove)
        fixed_Anime = ''.join(ch for ch in Anime if ch not in chars_to_remove)
        home_dir = os.path.expanduser("~")
        cache = f"{home_dir}/.animecache/{fixed_Anime}"
        os.makedirs(cache, exist_ok=True)
        logger.debug("Cache directory created at %s", cache)
        os.chdir(cache)
        m3u8_path = f"{fixed_Name}.m3u8"
        with open(m3u8_path, 'w', encoding='utf-8') as m3u8_writer:
            m3u8_writer.write(segments)
        logger.info("Wrote segments to %s", m3u8_path)
        
        # Import yt_dlp only for sync version
        import yt_dlp
        ydl_opts = {
            'outtmpl': f"{fixed_Name}.mkv",
            'quiet': False,
            'no_warnings': True,
            'merge_output_format': 'mkv',
            'http_headers': hd2_headers,
            'enable_file_urls': True,
            'concurrent_fragment_downloads': parallel,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info("Starting yt_dlp download for %s", m3u8_path)
            ydl.download([f"file:///{cache}/{fixed_Name}.m3u8"])
        os.remove(f"{cache}/{fixed_Name}.m3u8")
        logger.info("Removed temporary .m3u8 file: %s", m3u8_path)
        return 0
    except Exception as e:
        logger.error("Exception in downloading function: %s", e, exc_info=True)
        return 1