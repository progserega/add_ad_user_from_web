#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import psycopg2
import psycopg2.extras
import config as config
import logger as log

def get_ad_user_list():
	try:
		if config.DEBUG:
			log.add("connect to: dbname='" + config.user_list_db_name + "' user='" +config.user_list_db_user + "' host='" + config.user_list_db_host + "' password='" + config.user_list_db_passwd + "'")
		conn = psycopg2.connect("dbname='" + config.user_list_db_name + "' user='" +config.user_list_db_user + "' host='" + config.user_list_db_host + "' password='" + config.user_list_db_passwd + "'")
		cur = conn.cursor()
	except:
		log.add("I am unable to connect to the database");return False
	fio=familiya + " " + name + " " + otchestvo

	try:
		sql="""select
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
			add_ip,
			add_user_name
		from ad_users
		"""
		if config.DEBUG:
			log.add("sql=%s" % sql)
		cur.execute(sql)
		data = cur.fetchall()
	except:
		log.add("I am unable select data from db");return False
	user_list={}
	for line in data:
		user={}
		user["fio"]=line[0]
		user["name"]=line[1]
		user["familiya"]=line[2]
		user["otchestvo"]=line[3]
		user["login"]=line[4]
		user["old_login"]=line[5]
		user["passwd"]=line[6]
		user["drsk_email"]=line[7]
		user["drsk_email_passwd"]=line[8]
		user["rsprim_email"]=line[9]
		user["rsprim_email_passwd"]=line[10]
		user["hostname"]=line[11]
		user["ip"]=line[12]
		user["os"]=line[13]
		user["os_version"]=line[14]
		user["patches"]=line[15]
		user["doljnost"]=line[16]
		user["add_time"]=line[17]
		user["add_ip"]=line[18]
		user["add_user_name"]=line[19]
		user_list[user["login"]]=user
	return user_list

def add_ad_user(name, familiya, otchestvo, login, old_login, passwd, drsk_email, drsk_email_passwd, rsprim_email, rsprim_email_passwd, hostname, ip, os, os_version, patches, doljnost, add_ip, add_user_name):
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
			add_ip,
			add_user_name
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
			'%(add_ip)s',
			'%(add_user_name)s'
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
			"add_ip":add_ip,\
			"add_user_name":add_user_name\
		}
		if config.DEBUG:
			log.add("sql=%s" % sql)
		cur.execute(sql)
		conn.commit()
	except:
		log.add("I am unable insert data to db");return False
	return True
