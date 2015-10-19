#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import psycopg2
import psycopg2.extras
import config as config
import logger as log

STATUS_SUCCESS=0
STATUS_INTERNAL_ERROR=1
STATUS_USER_EXIST=2

def get_ad_user_list_by_fio():
	try:
		if config.DEBUG:
			log.add("user_ad_postgres_db.py get_ad_user_list_by_fio() connect to: dbname='" + config.user_list_db_name + "' user='" +config.user_list_db_user + "' host='" + config.user_list_db_host + "' password='" + config.user_list_db_passwd + "'")
		conn = psycopg2.connect("dbname='" + config.user_list_db_name + "' user='" +config.user_list_db_user + "' host='" + config.user_list_db_host + "' password='" + config.user_list_db_passwd + "'")
		cur = conn.cursor()
	except psycopg2.Error as e:
		log.add("user_ad_postgres_db.py get_ad_user_list_by_fio(): I am unable to connect to the database: %s" % e.pgerror);return False
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
			log.add("user_ad_postgres_db.py sql=%s" % sql)
		cur.execute(sql)
		data = cur.fetchall()
	except psycopg2.Error as e:
		log.add("user_ad_postgres_db.py I am unable select data from db: %s" % e.pgerror);return False
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
		user_list[user["fio"]]=user
	return user_list

def get_ad_user_list_by_login():
	try:
		if config.DEBUG:
			log.add("user_ad_postgres_db.py connect to: dbname='" + config.user_list_db_name + "' user='" +config.user_list_db_user + "' host='" + config.user_list_db_host + "' password='" + config.user_list_db_passwd + "'")
		conn = psycopg2.connect("dbname='" + config.user_list_db_name + "' user='" +config.user_list_db_user + "' host='" + config.user_list_db_host + "' password='" + config.user_list_db_passwd + "'")
		cur = conn.cursor()
	except psycopg2.Error as e:
		log.add("user_ad_postgres_db.py I am unable to connect to the database: %s" % e.pgerror);return False
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
			log.add("user_ad_postgres_db.py sql=%s" % sql)
		cur.execute(sql)
		data = cur.fetchall()
	except psycopg2.Error as e:
		log.add("user_ad_postgres_db.py I am unable select data from db: %s" % e.pgerror);return False
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
			log.add("user_ad_postgres_db.py connect to: dbname='" + config.user_list_db_name + "' user='" +config.user_list_db_user + "' host='" + config.user_list_db_host + "' password='" + config.user_list_db_passwd + "'")
		conn = psycopg2.connect("dbname='" + config.user_list_db_name + "' user='" +config.user_list_db_user + "' host='" + config.user_list_db_host + "' password='" + config.user_list_db_passwd + "'")
		cur = conn.cursor()
	except psycopg2.Error as e:
		log.add("user_ad_postgres_db.py I am unable to connect to the database: %s" % e.pgerror);return STATUS_INTERNAL_ERROR
		
	fio=familiya + " " + name + " " + otchestvo

	# Проверяем, есть ли уже такой:
	result=[]
	try:
		sql="""select rsprim_email from ad_users where rsprim_email='%(rsprim_email)s'""" \
			 % {\
				 "rsprim_email":rsprim_email \
			 }
		if config.DEBUG:
			log.add("user_ad_postgres_db.py user_ad_postgres_db.py add_ad_user() exec sql: %s" % sql)
		cur.execute(sql)
		result=cur.fetchall()
	except psycopg2.Error as e:
		log.add("user_ad_postgres_db.py ERROR postgres select: %s" %  e.pgerror)
		return STATUS_INTERNAL_ERROR
	if len(result) > 0:
		# Уже есть такой аккаунт:
		return STATUS_USER_EXIST

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
			log.add("user_ad_postgres_db.py sql=%s" % sql)
		cur.execute(sql)
		conn.commit()
	except psycopg2.Error as e:
		log.add("user_ad_postgres_db.py I am unable insert data to db: %s" % e.pgerror);return STATUS_INTERNAL_ERROR
	return STATUS_SUCCESS
