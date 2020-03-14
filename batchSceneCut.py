#!/usr/local/bin/python
# -*- coding:utf-8 -*-

# 1. for-in dir/subdir to get the filesname
# 2. splitext filename to filter

import argparse
import os
import threading
import time

from collections import defaultdict
from datetime import datetime
from subprocess import call, check_output
from time import sleep
from uuid import uuid1

# ffprobe -i clip.dv -show_format 2>&1 | grep 'duration='
duration_command = "ffprobe -hide_banner -i %s -show_format 2>&1 | grep 'duration='"

# ffprobe -show_frames -of compact=p=0 -f lavfi "movie=clip-135-02-05\ 05;27;15.dv,select=gt(scene\,.4)" > scenes.txt
probe_command = "ffprobe -hide_banner -show_frames -of compact=p=0 -f lavfi \"movie=%s,select=gt(scene\,.4)\" > %s 2>/dev/null"

# ffmpeg -i clip.dv -f segment -segment_times 7,20,47 -c copy -map 0:0 scenes/%04d.dv"""
extract_command = "ffmpeg -hide_banner -i %s -f segment -segment_times %s -c copy -map 0:0 -write_bext 1 %s/%s_%%04d.mxf 2>/dev/null"

# Define the command line parser
parser = argparse.ArgumentParser(description="This takes one large video file and creates smaller video files representing each scene in the original movie file.")
parser.add_argument("in_file", type=str, help="Name of the input path.")

def log_current_time():
  print datetime.now().isoformat()

def unescape(path):
  path = path.replace("\\ ", " ")
  return path

def path_exists(path):
  # ugh. unescape previously escaped spaces.
  path = unescape(path)
  return os.path.exists(path)

def seconds_to_timestamp(seconds):
  # calculate hours, minutes, seconds
  hours = 0
  minutes = seconds / 60
  if minutes > 60:
    hours = minutes / 60
    minutes = minutes % 60
  seconds = seconds % 60

  timestamp = "%02d:%02d:%02d" % (hours, minutes, seconds)
  return timestamp

def get_duration(filename):
  cmd = duration_command % (filename)
  #print cmd
  duration = check_output(cmd, shell=True)
  duration = duration.split("duration=")[1]

  # eliminate fractions of a second
  duration = duration.split(".")[0]
  duration = int(duration)
  return duration

def create_scenes_dir(filename):
  dir_name = get_dir(filename) + "/scenes"
  basename = os.path.basename(filename)
  basename, _ = os.path.splitext(basename)
  #print (basename)
  if path_exists(dir_name):
    print "Directory already exists: %s" % dir_name
  else:
    cmd = "mkdir %s" % (dir_name)
    call(cmd, shell=True)

  timestamps_txt = "%s/%s_timestamps.txt" % (dir_name, basename)
  if path_exists(timestamps_txt):
    print (timestamps_txt + " already exists")
  else:
    cmd = "touch %s" % (timestamps_txt)
    call(cmd, shell=True)

  return timestamps_txt

def is_timestamp(line):
  return "pkt_pts_time=" in line

def line_to_timestamp(line):
  # extract the timestamp from a line that looks like this:
  # media_type=video|key_frame=1|pkt_pts=94|pkt_pts_time=3.136467|pk...
  return float(line.split("time=")[1].split("|")[0])

def detect_scenes(filename, timestamps_txt, duration):
  scenes = []

  def probe():
    # probe the movie and create a text file containing timestamps of scene changes
    print ("Probing movie for scene changes...")
    cmd = probe_command % (filename, timestamps_txt)
    call(cmd, shell=True)

  def show_progress(timestamp):
    t1 = seconds_to_timestamp(timestamp)
    t2 = seconds_to_timestamp(duration)
    percent = 100 * (timestamp / duration)
    print "Found scene change at %s of %s (%02.2f%% complete)" % (t1, t2, percent)

  def poll():
    cmd = "cat %s" % (timestamps_txt)
    lines = check_output(cmd, shell=True)
    lines = lines.split("\n")
    lines = filter(is_timestamp, lines)

    timestamps = map(line_to_timestamp, lines)

    for timestamp in timestamps:
      if timestamp not in scenes:
        scenes.append(timestamp)
        show_progress(timestamp)

  prober = threading.Thread(target=probe)
  prober.start()

  while (prober.is_alive()):
    poll()
    sleep(1)

  print "Scene detection complete. %d scenes found." % (len(scenes))

  scenes.sort()
  return scenes

def extract_scenes(filename, scenes):
  print "Extracting scenes..."
  scenes = map(str, scenes)
  times = ",".join(scenes)
  basename = os.path.basename(filename)
  basename, _ = os.path.splitext(basename)
  scenes_dir = get_dir(filename) + "/scenes"
  cmd = extract_command % (filename, times, scenes_dir, basename)
  #print (cmd)
  call(cmd, shell=True)

def get_dir(filename):
  path = filename.split("/")
  return "/".join(path[:-1])

def getFiles(dir, suffix): 
    res = []
    files = os.listdir(dir)
    dir = dir + "/"
    for filename in files:
        name, suf = os.path.splitext(filename)
        if suf == suffix:
            res.append(os.path.join(dir, filename))
            #print (os.path.join(dir, filename))
    return res

def main():
	args = parser.parse_args()
	#print (args)
	dirname = args.in_file.replace(" ", "\\ ")
	#print (dirname)
	for filename in getFiles(dirname, '.mxf'):
		#print (filename)
		#log_current_time()
		print ("\033[32mProcessing %s \033[0m" %filename)
		duration = get_duration(filename)
		timestamps_txt = create_scenes_dir(filename)
		time.sleep(1)
		times = open(unescape(timestamps_txt)).readlines()
		if len(times) > 0:
			times = filter(is_timestamp, times)
			scenes = map(line_to_timestamp, times)
		else:
			#log_current_time()
			scenes = detect_scenes(filename, timestamps_txt, duration)

		#log_current_time()
		extract_scenes(filename, scenes)

main()
