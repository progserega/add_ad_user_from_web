#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cgi
import os
import time
import syslog
import ldap
import re
import subprocess
import sys
from ldap.controls import SimplePagedResultsControl
import ldap.modlist as modlist
import config as conf
import logger as log
import user_ad_postgres_db as ad_user_db
import add_to_email_db as email_db
import sendemail

SCRIPT = 1
ACCOUNTDISABLE = 2
HOMEDIR_REQUIRED = 8
LOCKOUT = 16
PASSWD_NOTREQD = 32
NORMAL_ACCOUNT = 512
DONT_EXPIRE_PASSWORD = 65536
TRUSTED_FOR_DELEGATION = 524288
PASSWORD_EXPIRED = 8388608

STATUS_SUCCESS=0
STATUS_INTERNAL_ERROR=1
STATUS_USER_EXIST=2
STATUS_USER_NOT_EXIST=3


def set_email_in_ad(username, email, domain=conf.domain, employee_num="1",base_dn=conf.base_user_dn,group_acl_base=conf.group_acl_base, group_rbl_base=conf.group_rbl_base):
	# LDAP connection
	try:
		# без ssl:
		#ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, 0)
		#ldap_connection = ldap.initialize(LDAP_SERVER)

		# ssl:
		#ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
		#ldap_connection = ldap.initialize(LDAP_SERVER)
		#ldap_connection.set_option(ldap.OPT_REFERRALS, 0)
		#ldap_connection.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
		#ldap_connection.set_option(ldap.OPT_X_TLS,ldap.OPT_X_TLS_DEMAND)
		#ldap_connection.set_option( ldap.OPT_X_TLS_DEMAND, True )
		#ldap_connection.set_option( ldap.OPT_DEBUG_LEVEL, 255 )
		ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
		ldap_connection = ldap.initialize(conf.LDAP_SERVER)
		ldap_connection.simple_bind_s(conf.BIND_DN, conf.BIND_PASS)
	except ldap.LDAPError, error_message:
		log.add(u"Error connecting to LDAP server: %s" % error_message)
		return STATUS_INTERNAL_ERROR

	# Check and see if user exists
	try:
		user_results = ldap_connection.search_s(base_dn, ldap.SCOPE_SUBTREE,
			'(&(sAMAccountName=' +
			username +
			')(objectClass=person))',
			['distinguishedName'])
	except ldap.LDAPError, error_message:
		log.add(u"Error finding username: %s" % error_message)
		return STATUS_INTERNAL_ERROR

	# Check the results
	if len(user_results) != 0:
		log.add(u"User %s already exists in AD:" % username )
#print "User", username, "already exists in AD:", \
		user_results[0][1]['distinguishedName'][0]
	else:
		return STATUS_USER_NOT_EXIST
	user_dn=user_results[0][0]

#unicode_email = unicode('\"' + email + '\"', 'iso-8859-1')
	unicode_email = unicode(email, 'iso-8859-1')
	email_value = unicode_email.encode('utf-16-le')
#mod_email = [(ldap.MOD_REPLACE, 'mail', [email_value])]
	mod_email = [(ldap.MOD_REPLACE, 'mail', email)]

	# mod the email:
	try:
		ldap_connection.modify_s(user_dn, mod_email)
	except ldap.LDAPError, error_message:
		log.add(u"Error modify email: %s" % error_message)
		return STATUS_INTERNAL_ERROR

	# LDAP unbind
	ldap_connection.unbind_s()

	return STATUS_SUCCESS

# ========== main ==============

users=ad_user_db.get_ad_user_list_by_login()
for login in users:
	user=users[login]
	if "drsk_email" in user:
		if len(user["drsk_email"])>0 and len(user["login"])>0: 
			print("""Пробуем присвоить почту %(drsk_email)s пользователю %(login)s""" % {"drsk_email":user["drsk_email"], "login":user["login"]})
			status=set_email_in_ad(username=user["login"], email=user["drsk_email"])
			if status == STATUS_SUCCESS:
				print("""УСПЕШНО присвоена почта %(drsk_email)s пользователю %(login)s""" % {"drsk_email":user["drsk_email"], "login":user["login"]})
			else:
				print("""ОШИБКА присвоения почты %(drsk_email)s пользователю %(login)s""" % {"drsk_email":user["drsk_email"], "login":user["login"]})
sys.exit(0)
