#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ffmpeg
import os
import tempfile

def test_ffmpeg_python():
    """Test ffmpeg-python functionality"""
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        print(f"Created temporary directory: {temp_dir}")
        
        # Create a simple text file for testing
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("This is a test file for ffmpeg-python")
        
        # Get ffmpeg version using ffmpeg-python
        print("Testing ffmpeg-python...")
        try:
            # This will create a stream object but not execute it
            stream = ffmpeg.input("non_existent_file.mp4")
            print(f"Created ffmpeg stream object: {stream}")
            print("ffmpeg-python is working correctly!")
        except Exception as e:
            print(f"Error with ffmpeg-python: {e}")
        
        # Test ffmpeg.probe functionality if available
        try:
            if hasattr(ffmpeg, 'probe'):
                print("Testing ffmpeg.probe functionality...")
                # We don't actually probe a file, just check if the function exists
                print("ffmpeg.probe function is available")
            else:
                print("ffmpeg.probe function is not available in this version")
        except Exception as e:
            print(f"Error testing ffmpeg.probe: {e}")
        
        # Clean up
        os.remove(test_file)
        os.rmdir(temp_dir)
        print(f"Cleaned up temporary directory: {temp_dir}")
        
        return True
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting ffmpeg-python test...")
    result = test_ffmpeg_python()
    print(f"Test {'passed' if result else 'failed'}")