#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import pymysql
import config as conf
import logger as log
import traceback

log = None
STATUS_SUCCESS=0
STATUS_INTERNAL_ERROR=1
STATUS_USER_EXIST=2

def get_exception_traceback_descr(e):
  if hasattr(e, '__traceback__'):
    tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
    result=""
    for msg in tb_str:
      result+=msg
    return result
  else:
    return "unknown error"
 
def get_users_phones_from_site(log_in):
  global log
  #  Начало 
  if log is None:
    log = log_in
  log.debug("start function")
  try:
    con = pymysql.connect(conf.user_phone_db_host, conf.user_phone_db_user, conf.user_phone_db_passwd, conf.user_phone_db_name, charset='cp1251');
    cur = con.cursor()
  except Exception as e:
    log.error("error mysql connect")
    log.error(get_exception_traceback_descr(e))
    return None

  users_phones={}
  sql="select name, phone, (select dolzh_name from ae_phone_dolzn where id=ae_phone_kadry.dolzh_id) as dolj, (select otdel_name from ae_phone_otdel where id=ae_phone_kadry.otdel1_id) as otdel,e_mail  from ae_phone_kadry"
  try:
    log.debug("sql=%s"%sql)
    cur.execute('SET NAMES cp1251')
    cur.execute(sql)
    data = cur.fetchall()
  except Exception as e:
    log.error("error mysql execute")
    log.error(get_exception_traceback_descr(e))
    return None

  for item in data:
    user={}
    try:
      if item[0] is not None:
        fio=item[0]
      else:
        user["fio"]="unknown"
      user["phone"]=item[1]
      if item[2] is not None:
        user["job"]=item[2]
      else:
        user["job"]=""
      if item[3] is not None:
        user["department"]=item[3]
      else:
        user["department"]=""
      if item[4] is not None:
        user["email"]=item[4]
      else:
        user["email"]=""
      users_phones[fio]=user
    except Exception as e:
      log.error(get_exception_traceback_descr(e))
      log.error("skip record for user with email: %s"%item[4])
      continue

  if con:    
    con.close()
  return users_phones
