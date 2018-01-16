#!/usr/bin/env python
# -*- coding: utf8 -*-

import datetime
from os import uname
import config as conf

def add(text, debug=False):
  outtext = u""
  nowtime = datetime.datetime.now()
  #outtext += u'\n' + (str(nowtime.strftime("%Y-%m-%d %H:%M:%S")) + ": " + text.decode('utf8'))
  outtext += u'\n' + (str(nowtime.strftime("%Y-%m-%d %H:%M:%S")) + ": " + text + u"\n")
  if debug:
	  print outtext,
  file_log_d = open(conf.log,'a')
  file_log_d.write(outtext.encode('utf8'))
  file_log_d.close()
