#!/usr/local/bin/python
# -*- coding:utf-8 -*-

# 1. for-in dir/subdir to get the filesname
# 2. splitext filename to filter

import argparse
import os
import threading
import time
import re
#import subprocess

from collections import defaultdict
from datetime import datetime
from subprocess import call, check_output
from time import sleep
from uuid import uuid1

duration_command = "ffprobe -hide_banner -i %s -show_format 2>&1"
probe_command = "ffmpeg -hide_banner -i %s -vf \"select=gt(scene\,0.4),showinfo\" -f null - 2>%s "
extract_command = "ffmpeg.exe -hide_banner -i %s -f segment -segment_times %s -c copy -map 0:0 -write_bext 1 %s\\%s_%s%%04d.mxf 2>nul"

# Define the command line parser
parser = argparse.ArgumentParser(description="This takes one large video file and creates smaller video files representing each scene in the original movie file.")
parser.add_argument("in_file", type=str, help="Name of the input path.")

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
  duration = ""
  duration = check_output(cmd, shell=True)
  duration = duration.decode()
  duration = duration.split("duration=")[1]
  duration = duration.split(".")[0]
  duration = int(duration)
  return duration

def create_scenes_dir(filename):
  dir_name = get_dir(filename) + "\\scenes"
  basename = os.path.basename(filename)
  basename, _ = os.path.splitext(basename)
  #print (basename)
  if path_exists(dir_name):
    print ("Directory already exists: %s" % dir_name)
  else:
    cmd = "mkdir %s" % (dir_name)
    call(cmd, shell=True)

  timestamps_txt = "%s\\%s_timestamps.txt" % (dir_name, basename)
  if path_exists(timestamps_txt):
    print (timestamps_txt + " already exists")
  else:
    cmd = "type null > %s 2>nul" % (timestamps_txt)
    call(cmd, shell=True)

  return timestamps_txt

def is_timestamp(line):
  return "pts_time:" in line

def line_to_timestamp(line):
  # extract the timestamp from a line that looks like this:
  # media_type=video|key_frame=1|pkt_pts=94|pkt_pts_time=3.136467|pk...
  return float(line.split("pts_time:")[1].split("p")[0])

def detect_scenes(filename, timestamps_txt, duration):
  scenes = []

  def probe():
    # probe the movie and create a text file containing timestamps of scene changes
    print ("Probing scene changes in %s" %filename)
    cmd = probe_command % (filename, timestamps_txt)
    call(cmd, shell=True)

  prober = threading.Thread(target=probe)
  prober.start()

  while (prober.is_alive()):
    sleep(1)
  times = open(unescape(timestamps_txt)).readlines()
  times = filter(is_timestamp, times)
  scenes = list(map(line_to_timestamp, times))
  print ("Scene detection complete. %d scenes found." % (len(scenes)))

  scenes.sort()
  return scenes

def extract_scenes(filename, scenes):
  basename = os.path.basename(filename)
  basename, _ = os.path.splitext(basename)
  scenes_dir = get_dir(filename) + "\\scenes"
  if len(scenes) > 650:
    i = 0
    while i*650+650 < len(scenes):
      print ("Extracting scenes: " + str(i) + '~' + str(i*650+650))
      scenesdo = scenes[i:i*650+650]
      scenesdo = map(str, scenesdo)
      times = ",".join(scenesdo)
      cmd = extract_command % (filename, times, scenes_dir, basename, i)
      #print (cmd)
      call(cmd, shell=True)
      #print (scenes_dir + '\\' + basename + '_' + str(i) + str(i*650+650).zfill(4) + '.mxf')
      os.remove(scenes_dir + '\\' + basename + '_' + str(i) + str(i*650+650).zfill(4) + '.mxf')
      i=i+1
    else:
      print ("Extracting scenes: " + str(i*650-1) + '~' + str(len(scenes)))
      scenesdo = scenes[i*650-1:]
      scenesdo = map(str, scenesdo)
      times = ",".join(scenesdo)
      cmd = extract_command % (filename, times, scenes_dir, basename, i)
      #print (cmd)
      call(cmd, shell=True)
      os.remove(scenes_dir + '\\' + basename + '_' + str(i) + '0000.mxf')
  else:
    print ("Extracting scenes...")
    scenes = map(str, scenes)
    times = ",".join(scenes)
    cmd = extract_command % (filename, times, scenes_dir, basename, 0)
    call(cmd, shell=True)

def get_dir(filename):
  path = filename.split("\\")
  return "\\".join(path[:-1])

def main():
  args = parser.parse_args()
  #print (args)
  filename = args.in_file.replace(" ", "\\ ")
  print ("Processing: %s" %filename)
  duration = get_duration(filename)
  timestamps_txt = create_scenes_dir(filename)
  times = open(unescape(timestamps_txt)).readlines()
  if len(times) > 0:
    times = filter(is_timestamp, times)
    scenes = list(map(line_to_timestamp, times))
  else:
    scenes = detect_scenes(filename, timestamps_txt, duration)
  extract_scenes(filename, scenes)

main()
