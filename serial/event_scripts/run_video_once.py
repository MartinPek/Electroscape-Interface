# sudo pip3 install python-vlc
# pip3 install -r requirements.txt

# from moviepy.editor import VideoFileClip
# from pymediainfo import MediaInfo
import subprocess
import os
from time import sleep

try:
    from event_scripts.run_video_cfg import Settings as cfg
except:
    from run_video_cfg import Settings as cfg


script_dir = os.path.dirname(__file__)

filename = cfg["filename"]
file_duration = int(cfg["file_duration"])


# optional stuff that used to work but bugger RPis not having codecs, not wasting half an hour on this when its not needed
'''
def get_video_length():
    print("checking filepath")
    print(os.path.exists(filename))
    print(filename)
    media_info = MediaInfo.parse(filename)
    # duration in milliseconds
    return media_info.tracks[0].duration
'''


def run_video():

    video_fullpath = os.path.join(script_dir, "event_files", filename)
    print(video_fullpath)
    
    if not os.path.exists(video_fullpath): 
        print("!Error invalid video path")

    #  --no-embedded-video
    video_process = subprocess.Popen(['/usr/bin/cvlc', video_fullpath, "--no-embedded-video", "--fullscreen"])

    sleep(file_duration)
    video_process.kill()


def main():
    run_video()


if __name__ == "__main__":
    # stuff only to run when not called via 'import' here
    main()


def __init__():
    print("run_video_once.py imported")