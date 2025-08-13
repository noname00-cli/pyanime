#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# test_streamer.py - Test the streaming functionality

import sys
import os
import json
import argparse

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from providers.Hianime.Streamer import stream_episode
from config.logging_config import get_logger

# Setup logging for this module
logger = get_logger("test_streamer")

def main():
    """Test the streaming functionality"""
    parser = argparse.ArgumentParser(description="Test anime streaming functionality")
    parser.add_argument("--episode-id", type=str, help="Episode ID (JSON string)")
    parser.add_argument("--server-type", type=str, default="sub", choices=["sub", "dub"], help="Server type (sub or dub)")
    parser.add_argument("--player", type=str, default="ffmpeg", choices=["ffmpeg", "vlc", "mpv"], help="Player to use")
    
    args = parser.parse_args()
    
    if not args.episode_id:
        # Example episode ID for testing - using a mock structure
        # This is just for testing the player functionality
        episode_id = {
            "Episode ID": "12345",
            "Title": "Test Episode",
            "URL": "/watch/test-episode"
        }
        
        # Create a mock stream data structure for testing
        # This will bypass the actual server extraction
        mock_stream_data = {
            "id": episode_id,
            "server": "SUB",
            "type": "sub",
            "link": {
                # Use a local test file or a known good stream URL
                "file": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
                "type": "hls",
            },
            "tracks": [],
            "intro": None,
            "outro": None,
        }
        
        # Import the streamer classes directly for testing
        from providers.Hianime.Streamer import FFmpegStreamer, LibVLCStreamer, MPVStreamer
        
        # Create the appropriate streamer based on player selection
        if args.player.lower() == "vlc":
            streamer = LibVLCStreamer(mock_stream_data)
        elif args.player.lower() == "mpv":
            streamer = MPVStreamer(mock_stream_data)
        else:  # Default to ffmpeg
            streamer = FFmpegStreamer(mock_stream_data)
        
        # Stream directly using the selected player
        success = streamer.stream()
    else:
        try:
            episode_id = json.loads(args.episode_id)
            # Stream the episode using the normal flow
            success = stream_episode(episode_id, args.server_type, args.player)
        except json.JSONDecodeError:
            logger.error("Invalid episode ID JSON")
            return 1
    
    logger.info(f"Testing streaming for episode: {episode_id.get('Title', 'Unknown')}")
    logger.info(f"Using server type: {args.server_type} and player: {args.player}")
    
    # Stream the episode
    success = stream_episode(episode_id, args.server_type, args.player)
    
    if success:
        logger.info("Streaming test completed successfully")
        return 0
    else:
        logger.error("Streaming test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())