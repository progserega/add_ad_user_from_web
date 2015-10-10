#!/usr/bin/env python
# -*- coding: utf8 -*-

import datetime
from os import uname
import config as conf

def add(text, debug=False):
  outtext = ''
  nowtime = datetime.datetime.now()
  outtext += '\n' + (str(nowtime.strftime("%Y-%m-%d %H:%M:%S")) + ": " + text.encode('utf8'))
  if debug:
	  print outtext,
  file_log_d = open(conf.log,'a')
  file_log_d.write(outtext+'\n')
  file_log_d.close()
