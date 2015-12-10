#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import ldap
import re
import config as conf

ldap_url=conf.LDAP_SERVER
ldap_user=conf.BIND_DN
ldap_passwd=conf.BIND_PASS

# Some flags for userAccountControl property
SCRIPT = 1
ACCOUNTDISABLE = 2
HOMEDIR_REQUIRED = 8
PASSWD_NOTREQD = 32
NORMAL_ACCOUNT = 512
DONT_EXPIRE_PASSWORD = 65536
TRUSTED_FOR_DELEGATION = 524288
PASSWORD_EXPIRED = 8388608


def init():
	global ldap_url
	global ldap_user
	global ldap_passwd

	try:
		# http:
		#ad = ldap.initialize(ldap_url)
		#ad.set_option(ldap.OPT_REFERRALS,0)
		#ad.simple_bind_s(ldap_user,ldap_passwd)

		# https:
		ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
		ad = ldap.initialize(conf.LDAP_SERVER)
		ad.simple_bind_s(conf.BIND_DN, conf.BIND_PASS)
	except ldap.LDAPError, desc:
		print("error", desc)
	return ad


def get_computers(ad):
	comps={}
	try:
		#basedn = 'DC=drsk,DC=rao-esv,DC=ru'
		basedn = conf.base_comp_dn
		scope = ldap.SCOPE_SUBTREE
		filterexp = '(&(objectCategory=Computer)(objectClass=Computer)(cn=RSK40*))'
		attrlist = ['cn','description']
		results = ad.search_s(basedn, scope, filterexp, attrlist)
		#print(results)
	except ldap.LDAPError, desc:
		print("error", desc)

	for result in results:
			comp={}
			comp["name"]=result[1]['cn'][0]
			comp["full_name"]="%s.drsk.rao-esv.ru" % result[1]['cn'][0].lower()
			if "description" in result[1]:
				comp["description"]=result[1]['description'][0]
			comps[comp["name"]]=comp
	return comps

def get_users(ad):
	users={}
	try:
		#basedn = 'DC=drsk,DC=rao-esv,DC=ru'
		basedn = conf.base_user_dn
		scope = ldap.SCOPE_SUBTREE
		filterexp = '(sAMAccountName=*)'
		attrlist = ['sAMAccountName','description','givenName','sn','mail','userWorkstations','initials','displayName','info','displayNamePrintable','canonicalName','ms-DS-UserAccountAutoLocked','msDS-UserAccountDisabled','msDS-UserDontExpirePassword','msDS-UserPasswordExpired','UserAccountControl']
		#attrlist = ['cn']
		results = ad.search_s(basedn, scope, filterexp, attrlist)
	except ldap.LDAPError, desc:
		print("error", desc)

	for result in results:
	#		print(result)
			user={}
			user["account_name"]=result[1]['sAMAccountName'][0]
			user["attr"]=int(result[1]['userAccountControl'][0])
			if "givenName" in result[1]:
				user["firstname"]=result[1]['givenName'][0]
			if "description" in result[1]:
				user["description"]=result[1]['description'][0]
			if "sn" in result[1]:
				user["secondname"]=result[1]['sn'][0]
			if "mail" in result[1]:
				user["mail"]=result[1]['mail'][0]
			if "canonicalName" in result[1]:
				user["full_name"]=re.sub(r'.*/','',result[1]['canonicalName'][0])
			users[user["account_name"]]=user

		#	for key in result[1]:
		#		print("%s = %s" %(key,result[1][key][0]))

		#	for key in user:
		#		print("user: %s = %s" % (key, user[key]))
	return users

#t=0
#print("t=",t)
#print("t=",t | 1 << 3)





