#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import psycopg2
import psycopg2.extras
import config as config
import logger as log

def add_ad_user(name, familiya, otchestvo, login, old_login, passwd, drsk_email, drsk_email_passwd, rsprim_email, rsprim_email_passwd, hostname, ip, os, os_version, patches, doljnost, add_ip):
	try:
		if config.DEBUG:
			log.add("connect to: dbname='" + config.user_list_db_name + "' user='" +config.user_list_db_user + "' host='" + config.user_list_db_host + "' password='" + config.user_list_db_passwd + "'")
		conn = psycopg2.connect("dbname='" + config.user_list_db_name + "' user='" +config.user_list_db_user + "' host='" + config.user_list_db_host + "' password='" + config.user_list_db_passwd + "'")
		cur = conn.cursor()
	except:
		log.add("I am unable to connect to the database");return False
		
	fio=familiya + " " + name + " " + otchestvo

	try:
		sql="""insert into ad_users (
			fio,
			name,
			familiya,
			otchestvo,
			login,
			old_login,
			passwd,
			drsk_email,
			drsk_email_passwd,
			rsprim_email,
			rsprim_email_passwd,
			hostname,
			ip,
			os,
			os_version,
			patches,
			doljnost,
			add_time,
			add_ip
		) 
		VALUES (
			'%(fio)s',
			'%(name)s',
			'%(familiya)s',
			'%(otchestvo)s',
			'%(login)s',
			'%(old_login)s',
			'%(passwd)s',
			'%(drsk_email)s',
			'%(drsk_email_passwd)s',
			'%(rsprim_email)s',
			'%(rsprim_email_passwd)s',
			'%(hostname)s',
			'%(ip)s',
			'%(os)s',
			'%(os_version)s',
			'%(patches)s',
			'%(doljnost)s',
			now(),
			'%(add_ip)s
		)""" % \
		{\
			"fio":fio,\
			"name":name,\
			"familiya":familiya,\
			"otchestvo":otchestvo,\
			"login":login,\
			"old_login":old_login,\
			"passwd":passwd,\
			"drsk_email":drsk_email,\
			"drsk_email_passwd":drsk_email_passwd,\
			"rsprim_email":rsprim_email,\
			"rsprim_email_passwd":rsprim_email_passwd,\
			"hostname":hostname,\
			"ip":ip,\
			"os":os,\
			"os_version":os_version,\
			"patches":patches,\
			"doljnost":doljnost,\
			"add_ip":add_ip\
		}
		if config.DEBUG:
			log.add("sql=%s" % sql)
		cur.execute(sql)
		conn.commit()
	except:
		log.add("I am unable insert data to db");return False
	return True
