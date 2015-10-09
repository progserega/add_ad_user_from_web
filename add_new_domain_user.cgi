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

SCRIPT = 1
ACCOUNTDISABLE = 2
HOMEDIR_REQUIRED = 8
LOCKOUT = 16
PASSWD_NOTREQD = 32
NORMAL_ACCOUNT = 512
DONT_EXPIRE_PASSWORD = 65536
TRUSTED_FOR_DELEGATION = 524288
PASSWORD_EXPIRED = 8388608

def create_drsk_user(user_familia,user_name,user_otchestvo,description, user):
	fam=user_familia
	name=user_name
	otch=user_otchestvo
	fio=fam + " " + name + " " + otch
	login=rus2en(fam.lower()) + "_" + rus2en(name[0].lower()) + rus2en(otch[0].lower())  
	email_prefix=rus2en(fam.lower()) + "-" + rus2en(name[0].lower()) + rus2en(otch[0].lower())  
	email_server1=email_prefix+conf.email_server1_postfix
	email_server2=email_prefix+conf.email_server2_postfix
	passwd=get_passwd()

	if conf.DEBUG:
		print(u"==============================================")
		print(u"ФИО: %s" % fio )
		print(u"Логин: %s" % login)
		print(u"Пароль: '%s'" % passwd)
		print(u"Почта префикс: %s" % email_prefix)
		print(u"Почта ДРСК: %s" % email_server1)
		print(u"Почта rsprim: %s" % email_server2)
		print(u"")
	user["fio"]=fio
	user["login"]=login
	user["passwd"]=passwd
	user["email_prefix"]=email_prefix
	user["email_server1"]=email_server1
	user["email_server2"]=email_server2
	if CreateADUser(login, passwd, name.encode('utf8'), fam.encode('utf8'), otch.encode('utf8'), description.encode('utf8'), acl_groups=conf.default_acl_groups,domain=conf.domain, employee_num="1",base_dn=conf.base_user_dn,group_acl_base=conf.group_acl_base) is False:
		return False
	return True


def CreateADUser(username, password, name, familiya, otchestvo, description, acl_groups,domain=conf.domain, employee_num="1",base_dn=conf.base_user_dn,group_acl_base=conf.group_acl_base):
	"""
	Create a new user account in Active Directory.
	"""
	fname=name
	lname=familiya

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
		print "Error connecting to LDAP server: %s" % error_message
		return False

	# Check and see if user exists
	try:
		user_results = ldap_connection.search_s(base_dn, ldap.SCOPE_SUBTREE,
			'(&(sAMAccountName=' +
			username +
			')(objectClass=person))',
			['distinguishedName'])
	except ldap.LDAPError, error_message:
		print "Error finding username: %s" % error_message
		return False

	# Check the results
	if len(user_results) != 0:
		print "User", username, "already exists in AD:", \
		user_results[0][1]['distinguishedName'][0]
		return False

	# Lets build our user: Disabled to start (514)
	user_dn = 'cn=' + fname + ' ' + lname + ',' + base_dn
	user_attrs = {}
	user_attrs['objectClass'] = \
	['top', 'person', 'organizationalPerson', 'user']
	user_attrs['cn'] = fname + ' ' + lname
	user_attrs['userPrincipalName'] = username + '@' + domain
	user_attrs['sAMAccountName'] = username
	user_attrs['givenName'] = fname
	user_attrs['sn'] = lname
	user_attrs['displayName'] = familiya + ' ' + name + ' ' + otchestvo
	user_attrs['displayNamePrintable'] = familiya + ' ' + name + ' ' + otchestvo
	user_attrs['description'] = description
	#user_attrs['userAccountControl'] = '514'
	user_attrs['userAccountControl'] = "%d" % (NORMAL_ACCOUNT + DONT_EXPIRE_PASSWORD + ACCOUNTDISABLE)
	#user_attrs['mail'] = username + '@host.com'
	user_attrs['employeeID'] = employee_num
	#user_attrs['homeDirectory'] = '\\\\server\\' + username
	#user_attrs['homeDrive'] = 'H:'
	#user_attrs['scriptPath'] = 'logon.vbs'
	user_ldif = modlist.addModlist(user_attrs)

	# Prep the password
	unicode_pass = unicode('\"' + password + '\"', 'iso-8859-1')
	password_value = unicode_pass.encode('utf-16-le')
	#password_value = unicode_pass.encode('utf-16').lstrip('\377\376')
	add_pass = [(ldap.MOD_REPLACE, 'unicodePwd', [password_value])]
	# 512 will set user account to enabled
	mod_acct = [(ldap.MOD_REPLACE, 'userAccountControl', "%d" % ( NORMAL_ACCOUNT + DONT_EXPIRE_PASSWORD) )]
	#mod_acct = [(ldap.MOD_REPLACE, 'userAccountControl', "512" )]
	# New group membership
	add_member = [(ldap.MOD_ADD, 'member', user_dn)]
	# Replace the primary group ID
	#mod_pgid = [(ldap.MOD_REPLACE, 'primaryGroupID', GROUP_TOKEN)]
	# Delete the Domain Users group membership
	#del_member = [(ldap.MOD_DELETE, 'member', user_dn)]

	# Add the new user account
	try:
		ldap_connection.add_s(user_dn, user_ldif)
	except ldap.LDAPError, error_message:
		print "Error adding new user: %s" % error_message
		return False

	# Add the password
	try:
		ldap_connection.modify_s(user_dn, add_pass)
	except ldap.LDAPError, error_message:
		print "Error setting password: %s" % error_message
		return False

	# Change the account back to enabled
	try:
		ldap_connection.modify_s(user_dn, mod_acct)
	except ldap.LDAPError, error_message:
		print "Error enabling user: %s" % error_message
		return False

	# Add user to their primary group
	for acl_group in acl_groups:
		GROUP_DN="CN="+acl_group+","+ group_acl_base
		try:
			ldap_connection.modify_s(GROUP_DN, add_member)
		except ldap.LDAPError, error_message:
			print "Error adding user to group: %s" % error_message
			return False

	# Modify user's primary group ID
	#try:
	#    ldap_connection.modify_s(user_dn, mod_pgid)
	#except ldap.LDAPError, error_message:
	#    print "Error changing user's primary group: %s" % error_message
	#    return False

	# Remove user from the Domain Users group
	#try:
	#    ldap_connection.modify_s(DU_GROUP_DN, del_member)
	#except ldap.LDAPError, error_message:
	#    print "Error removing user from group: %s" % error_message
	#    return False

	# LDAP unbind
	ldap_connection.unbind_s()

	# Setup user's home directory
	#os.system('mkdir -p /home/' + username + '/public_html')
	#os.system('cp /etc/skel/.bashrc /etc/skel/.bash_profile ' +
	#          '/etc/skel/.bash_logout /home/' + username)
	#os.system('chown -R ' + username + ' /home/' + username)
	#os.system('chmod 0701 /home/' + username)

	# All is good
	return True

def get_passwd():
	t = subprocess.Popen(("pwgen","-s" ,"8", "1"), stderr=subprocess.PIPE,stdout=subprocess.PIPE)
	ret_code=t.wait()
	t_stdout_list=t.stdout.readlines()
	return t_stdout_list[0].strip('\n')

def rus2en(string):
	r2e={}
	r2e[u"0"]="0"
	r2e[u"1"]="1"
	r2e[u"2"]="2"
	r2e[u"3"]="3"
	r2e[u"4"]="4"
	r2e[u"5"]="5"
	r2e[u"6"]="6"
	r2e[u"7"]="7"
	r2e[u"8"]="8"
	r2e[u"9"]="9"
	r2e[u"_"]="_"
	r2e[u" "]=" "
	r2e[u"А"]="A"
	r2e[u"Б"]="B"
	r2e[u"В"]="V"
	r2e[u"Г"]="G"
	r2e[u"Д"]="D"
	r2e[u"Е"]="E"
	r2e[u"Ё"]="E"
	r2e[u"Ж"]="Zh"
	r2e[u"З"]="Z"
	r2e[u"И"]="I"
	r2e[u"Й"]="I"
	r2e[u"К"]="K"
	r2e[u"Л"]="L"
	r2e[u"М"]="M"
	r2e[u"Н"]="N"
	r2e[u"О"]="O"
	r2e[u"П"]="P"
	r2e[u"Р"]="R"
	r2e[u"С"]="S"
	r2e[u"Т"]="T"
	r2e[u"У"]="U"
	r2e[u"Ф"]="F"
	r2e[u"Х"]="Kh"
	r2e[u"Ц"]="Ts"
	r2e[u"Ч"]="Ch"
	r2e[u"Ш"]="Sh"
	r2e[u"Щ"]="Shch"
	r2e[u"Ъ"]="Ie"
	r2e[u"Ы"]="Y"
	r2e[u"Ь"]="-"
	r2e[u"Э"]="E"
	r2e[u"Ю"]="Iu"
	r2e[u"Я"]="Ia"
	r2e[u"а"]="a"
	r2e[u"б"]="b"
	r2e[u"в"]="v"
	r2e[u"г"]="g"
	r2e[u"д"]="d"
	r2e[u"е"]="e"
	r2e[u"ё"]="e"
	r2e[u"ж"]="zh"
	r2e[u"з"]="z"
	r2e[u"и"]="i"
	r2e[u"й"]="i"
	r2e[u"к"]="k"
	r2e[u"л"]="l"
	r2e[u"м"]="m"
	r2e[u"н"]="n"
	r2e[u"о"]="o"
	r2e[u"п"]="p"
	r2e[u"р"]="r"
	r2e[u"с"]="s"
	r2e[u"т"]="t"
	r2e[u"у"]="u"
	r2e[u"ф"]="f"
	r2e[u"х"]="kh"
	r2e[u"ц"]="ts"
	r2e[u"ч"]="ch"
	r2e[u"ш"]="sh"
	r2e[u"щ"]="shch"
	r2e[u"ъ"]="ie"
	r2e[u"ы"]="y"
	r2e[u"ь"]="-"
	r2e[u"э"]="e"
	r2e[u"ю"]="iu"
	r2e[u"я"]="ia"

	result=""
	for bukva in string:
		if r2e[bukva] != "-":
			result=result+r2e[bukva]
	return result



# ========== main ==============
if conf.DEBUG:
	user_familia = u"Фамилия"
	user_name = u"Имя"
	user_otchestvo = u"Отчество"
	user_description = u"(А - для сортировки) описание"
else:
	form = cgi.FieldStorage()

	user_agent=os.getenv("HTTP_USER_AGENT")
	user_addr=os.getenv("REMOTE_ADDR")
	user_host=os.getenv("REMOTE_HOST")

	print("""
	<html>
	<head>
	<meta http-equiv='Content-Type' content='text/html; charset=utf-8'>
	<title>Результат выполнения</title>
	</head>
	<body>
	""" )

	# Поле 'work_sites_regex' содержит не пустое значение:
	if 'user_familia' in form and 'user_name' in form and 'user_otchestvo' in form and 'user_description' in form:
		user_familia = u"%s" % cgi.escape(form['user_familia'].value.decode('utf8'))
		user_name = u"%s" % cgi.escape(form['user_name'].value.decode('utf8'))
		user_otchestvo = u"%s" % cgi.escape(form['user_otchestvo'].value.decode('utf8'))
		user_description = u"%s" % cgi.escape(form['user_description'].value.decode('utf8'))
	else:
		print("Необходимо заполнить все поля")
		print("</body></html>")
		sys.exit(1)
log.add("try create user: %s, %s, %s, %s" % (user_familia, user_name, user_otchestvo, user_description) )

# Обрабатываем ФИО - добавляем пользователя и выводим на экран результат:
user={}
if create_drsk_user(user_familia,user_name,user_otchestvo,user_description,user) is False:
	log.add("ERROR create user: %s, %s, %s, %s" % (user_familia, user_name, user_otchestvo, user_description) )
	print("Внутренняя ошибка!")
	print("</body></html>")
	sys.exit(1)
else:
	# Всё хорошо, печатаем результат:
	print("""<h2>Успешно создан пользователь:</h2>""")
	print("""<h2>Успешно создан пользователь:</h2>""")
	print("""<h2>Имя: %s</h2>""" % user["fio"].encode('utf8'))
	print("""<h2>Логин: %s</h2>""" % user["login"].encode('utf8'))
	print("""<h2>Имя: %s</h2>""" % user["passwd"].encode('utf8'))
	print("""<h2>Имя: %s</h2>""" % user["email_prefix"].encode('utf8'))
	print("""<h2>Имя: %s</h2>""" % user["email_server1"].encode('utf8'))
	print("""<h2>Имя: %s</h2>""" % user["email_server2"].encode('utf8'))
	print("</body></html>")
	log.add("SUCCESS create user: (%(user_familia)s, %(user_name)s, %(user_otchestvo)s, %(user_description)s),\
 login: %(login)s, passwd: '%(passwd)s', email_server1: %(email_server1)s, email_server2: %(email_server2)s"
		% {
		"user_familia":user_familia,
		"user_name":user_name,
		"user_otchestvo":user_otchestvo,
		"user_description":user_description,
		"login":user["login"],
		"passwd":user["passwd"],
		"email_server1":user["email_server1"],
		"email_server2":user["email_server2"]
		})
	sys.exit(0)
