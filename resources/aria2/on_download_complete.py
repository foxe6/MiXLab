#!/usr/bin/python3
import sys
import time


download_id = sys.argv[1]
num_files = sys.argv[2]
first_file = sys.argv[3]
open("/content/aria2_complete.log", "ab").write("{ }{} {} {}\n".format(time.time(), download_id, num_files, first_file).encode())
