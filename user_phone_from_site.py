#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import MySQLdb as mdb
import config as conf
import logger as log
import traceback

STATUS_SUCCESS=0
STATUS_INTERNAL_ERROR=1
STATUS_USER_EXIST=2
 
def get_exception_traceback_descr(e):
  tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
  result=""
  for msg in tb_str:
    result+=msg
  return result

def get_users_phones_from_site():
  #  Начало 
  log.add("get_users_phones_from_site()")
  try:
    con = mdb.connect(conf.user_phone_db_host, conf.user_phone_db_user, conf.user_phone_db_passwd, conf.user_phone_db_name);
    cur = con.cursor()
  except mdb.Error, e:
    print "Error %d: %s" % (e.args[0],e.args[1])
    log.add("error connect to mysql user phone db: %d: %s" % (e.args[0],e.args[1]))
    sys.exit(1)

  users_phones={}
  sql="select name, phone, (select dolzh_name from ae_phone_dolzn where id=ae_phone_kadry.dolzh_id) as dolj, (select otdel_name from ae_phone_otdel where id=ae_phone_kadry.otdel1_id) as otdel,e_mail  from ae_phone_kadry"
  try:
    cur.execute('SET NAMES cp1251')
    cur.execute(sql)
    data = cur.fetchall()
  except mdb.Error, e:
    print "Error %d: %s" % (e.args[0],e.args[1])
    log.add("error connect to mysql user phone db: %d: %s" % (e.args[0],e.args[1]))
    sys.exit(1)

  for item in data:
    user={}
    try:
      fio=item[0].decode("cp1251").encode("utf-8")
      user["fio"]=fio
      user["phone"]=item[1]
      user["job"]=item[2].decode("cp1251").encode("utf-8")
      user["department"]=item[3].decode("cp1251").encode("utf-8")
      user["email"]=item[4]
      users_phones[fio]=user
    except Exception as e:
      log.add(get_exception_traceback_descr(e))
      log.add("skip record for user with email: %s"%item[4])
      continue

  if con:    
    con.close()
	return users_phones
