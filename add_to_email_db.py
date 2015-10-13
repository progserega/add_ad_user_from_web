#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import time
import datetime
import MySQLdb as mdb
import os
import config as conf
import logger as log

def add_user_to_exim_db(db_host, db_name, db_user, db_passwd, email_prefix, email_domain, email_passwd, email_descr):
	try:
		con = mdb.connect(db_host, db_user, db_passwd, db_name);
		cur = con.cursor()
	except mdb.Error, e:
		log.add("ERROR mysql connect: %d: %s" % (e.args[0],e.args[1]))
		return False

	# Добавляем ящик:
	try:
		sql="""insert into mailbox (username, password, name, maildir, quota, local_part, domain, created, modified, active ) VALUES ( '%(username)s', '%(password)s', '%(name)s', '%(maildir)s', %(quota)s, '%(local_part)s', '%(domain)s', now(), now(), 1 )""" \
			 % {\
				 "username":mdb.escape_string(email_prefix + "@" + email_domain), \
				 "password":mdb.escape_string(email_passwd), \
				 "name":mdb.escape_string(email_descr), \
				 "maildir":"%"mdb.escape_string(email_domain + "/" + email_prefix + "/"), \
				 "quota":"0", \
				 "local_part":mdb.escape_string(email_prefix), \
				 "domain":mdb.escape_string(email_domain) \
			 }
		if conf.DEBUG:
			log.add("add_to_email_db.py add_user_to_exim_db() exec sql: %s" % sql)
		cur.execute(sql)
		con.commit()
	except mdb.Error, e:
		log.add("ERROR mysql insert: %d: %s" % (e.args[0],e.args[1]))
		return False

	# В алиасы:
	try:
		sql="""insert into alias (address, goto, domain, created, modified, active) VALUES ('%(address)s','%(goto)s', '%(domain)s', now(), now(), 1 )""" \
			 % {\
				 "address":email_prefix + "@" + email_domain, \
				 "goto":email_prefix + "@" + email_domain, \
				 "domain":email_domain \
			 }
		if conf.DEBUG:
			log.add("add_to_email_db.py add_user_to_exim_db() exec sql: %s" % sql)
		cur.execute(sql)
		con.commit()
	except mdb.Error, e:
		log.add("ERROR mysql insert: %d: %s" % (e.args[0],e.args[1]))
		return False
	
	log.add(" success add email account to: %s@%s" % email_prefix + "@" + email_domain)
	return True
		
