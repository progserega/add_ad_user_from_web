#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import time
import datetime
import pymysql
import os
import config as conf
import logging
from logging import handlers
import traceback

STATUS_SUCCESS=0
STATUS_INTERNAL_ERROR=1
STATUS_USER_EXIST=2

log = None

def get_exception_traceback_descr(e):
  if hasattr(e, '__traceback__'):
    tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
    result=""
    for msg in tb_str:
      result+=msg
    return result
  else:
    return "unknown error"

def add_user_to_exim_db(log_in, db_host, db_name, db_user, db_passwd, email_prefix, email_domain, email_passwd, email_descr):
  global log
  if log is None:
    log=log_in
  try:
    con = pymysql.connect(host=db_host, user=db_user, passwd=db_passwd, db=db_name, charset='utf8', init_command='SET NAMES UTF8');
    cur = con.cursor()
  except pymysql.Error as e:
    log.error("ERROR mysql connect: %d: %s" % (e.args[0],e.args[1]))
    return STATUS_INTERNAL_ERROR

  # Проверяем, есть ли уже такой:
  result=[]
  try:
    sql="""select username from mailbox where username='%(username)s'""" \
       % {\
         "username":pymysql.escape_string(email_prefix + "@" + email_domain) \
       }
    log.debug("add_to_email_db.py add_user_to_exim_db() exec sql: %s" % sql.decode('utf8'))
    cur.execute(sql)
    result=cur.fetchall()
  except pymysql.Error as e:
    log.error("ERROR mysql insert: %d: %s" % (e.args[0],e.args[1]))
    return STATUS_INTERNAL_ERROR
  if len(result) > 0:
    # Уже есть такой аккаунт:
    return STATUS_USER_EXIST

  # Добавляем ящик:
  try:
    sql="""insert into mailbox (username, password, name, maildir, quota, local_part, domain, created, modified, active ) VALUES ( '%(username)s', '%(password)s', '%(name)s', '%(maildir)s', %(quota)s, '%(local_part)s', '%(domain)s', now(), now(), 1 )""" \
       % {\
         "username":pymysql.escape_string(email_prefix + "@" + email_domain), \
         "password":pymysql.escape_string(email_passwd), \
         "name":pymysql.escape_string(email_descr), \
         "maildir":pymysql.escape_string(email_domain + "/" + email_prefix + "/"), \
         "quota":"0", \
         "local_part":pymysql.escape_string(email_prefix), \
         "domain":pymysql.escape_string(email_domain) \
       }
    log.debug("add_to_email_db.py add_user_to_exim_db() exec sql: %s" % sql.decode('utf8'))
    cur.execute(sql)
    con.commit()
  except pymysql.Error as e:
    log.error("ERROR mysql insert: %d: %s" % (e.args[0],e.args[1]))
    return STATUS_INTERNAL_ERROR

  # В алиасы:
  try:
    sql="""insert into alias (address, goto, domain, created, modified, active) VALUES ('%(address)s','%(goto)s', '%(domain)s', now(), now(), 1 )""" \
       % {\
         "address":email_prefix + "@" + email_domain, \
         "goto":email_prefix + "@" + email_domain, \
         "domain":email_domain \
       }
    log.debug("add_to_email_db.py add_user_to_exim_db() exec sql: %s" % sql.decode('utf8'))
    cur.execute(sql)
    con.commit()
  except pymysql.Error as e:
    log.error("ERROR mysql insert: %d: %s" % (e.args[0],e.args[1]))
    return STATUS_INTERNAL_ERROR
  
  log.info(" success add email account to: %s@%s" % (email_prefix, email_domain))
  return STATUS_SUCCESS
