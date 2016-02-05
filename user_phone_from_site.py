#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import MySQLdb as mdb
import config as conf
import logger as log

STATUS_SUCCESS=0
STATUS_INTERNAL_ERROR=1
STATUS_USER_EXIST=2

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
	sql="select name, phone, (select dolzh_name from ae_phone_dolzn where id=ae_phone_kadry.dolzh_id) as dolj, (select otdel_name from ae_phone_otdel where id=ae_phone_kadry.otdel1_id) as otdel  from ae_phone_kadry"
	try:
		cur.execute(sql)
		data = cur.fetchall()
	except mdb.Error, e:
		print "Error %d: %s" % (e.args[0],e.args[1])
		log.add("error connect to mysql user phone db: %d: %s" % (e.args[0],e.args[1]))
		sys.exit(1)

	for item in data:
		user={}
		user["fio"]=item[0]
		user["phone"]=item[1]
		user["job"]=item[2]
		user["department"]=item[3]
		users_phones[fio]=user

	if con:    
		con.close()
	return users_phones
