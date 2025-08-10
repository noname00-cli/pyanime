import subprocess
import os

def test_ffmpeg():
    print("Testing FFmpeg subprocess call...")
    try:
        # Create a simple test file
        with open("test_file.txt", "w") as f:
            f.write("This is a test file.")
        
        # Run a simple FFmpeg command
        cmd = ["ffmpeg", "-version"]
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("FFmpeg version command executed successfully.")
        print(result.stdout.decode('utf-8')[:100] + "...")
        
        return True
    except Exception as e:
        print(f"Error testing FFmpeg: {e}")
        return False

if __name__ == "__main__":
    test_ffmpeg()