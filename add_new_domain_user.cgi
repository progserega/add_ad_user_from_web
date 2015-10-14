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

def create_drsk_user(user_familia,user_name,user_otchestvo,description, company, user):
	num_op=0
	num_success_op=0

	fam=user_familia
	name=user_name
	otch=user_otchestvo
	fio=fam + " " + name + " " + otch
	login=rus2en(fam.lower()) + "_" + rus2en(name.lower())[0] + rus2en(otch.lower())[0]  
	email_prefix=rus2en(fam.lower()) + "-" + rus2en(name.lower())[0] + rus2en(otch.lower())[0]  
	email_server1=email_prefix+"@"+conf.email_server1_domain
	email_server2=email_prefix+"@"+conf.email_server2_domain
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
	user["name"]=user_name
	user["familiya"]=user_familia
	user["otchestvo"]=user_otchestvo
	user["login"]=login
	user["passwd"]=passwd
	user["email_prefix"]=email_prefix
	user["email_server1"]=email_server1
	user["email_server2"]=email_server2
	user["description"]=description
	num_op+=1
	status=CreateADUser(login, passwd, name.encode('utf8'), fam.encode('utf8'), otch.encode('utf8'), description.encode('utf8'), company.encode('utf8'), acl_groups=conf.default_acl_groups,domain=conf.domain, employee_num="1",base_dn=conf.base_user_dn,group_acl_base=conf.group_acl_base)
	if status == STATUS_SUCCESS:
		num_success_op+=1
		print("""<p>УСПЕШНО заведён пользователь %s в домене""" % login.encode('utf8'))
		log.add(u"""SUCCESS - успешно заведенна учётная запись '%s' в домене""" % login) 
	elif status == STATUS_USER_EXIST:
		print("""<p>ОШИБКА заведения учётной записи '%s' в домене - пользователь УЖЕ СУЩЕСТВУЕТ</p>""" % login) 
		log.add(u"""ERROR USER EXIST - ошибка заведения учётной записи '%s' в домене - пользователь УЖЕ СУЩЕСТВУЕТ""" % login) 
	else:
		print("""<p>ОШИБКА заведения учётной записи '%s' в домене</p>""" % login) 
		log.add(u"""ERROR - ошибка заведения учётной записи '%s' в домене""" % login) 

	#=============================  Добавляем в почтовые сервера: ========================
	create_email=False
	try:
		if conf.db_email_server1_passwd is not None:
			create_email=True
	except:
		log.add(u"NOTICE: conf.db_email_server1_passwd is not defined - skip add email to server1")
	if create_email:
		num_op+=1
		status=email_db.add_user_to_exim_db(db_host=conf.db_email_server1_host, db_name=conf.db_email_server1_name, db_user=conf.db_email_server1_user, db_passwd=conf.db_email_server1_passwd, email_prefix=email_prefix, email_domain=conf.email_server1_domain, email_passwd=passwd, email_descr=fio)
		if status == STATUS_SUCCESS:
			log.add(u"SUCCESS add email to server: %s, %s" % (conf.db_email_server1_host, "%s@%s" % (email_prefix,conf.email_server1_domain)))
			print("""<p>УСПЕШНО заведён ящик %s@%s на сервере %s</p>""" % (email_prefix,conf.email_server1_domain,conf.db_email_server1_host))
			num_success_op+=1
		elif status == STATUS_USER_EXIST:
			log.add(u"ERROR USER EXIST  - add email to server: %s, %s failed - mailbox exist!" % (conf.db_email_server1_host, "%s@%s" % (email_prefix,conf.email_server1_domain)))
			print("""<p>ОШИБКА заведения ящика %s@%s на сервере %s - ящик УЖЕ СУЩЕСТВУЕТ</p>""" % (email_prefix,conf.email_server1_domain,conf.db_email_server1_host))
		else:
			log.add(u"ERROR add email to server: %s, %s" % (conf.db_email_server1_host, "%s@%s" % (email_prefix,conf.email_server1_domain)))
			print("""<p>ОШИБКА заведения ящика %s@%s на сервере %s</p>""" % (email_prefix,conf.email_server1_domain,conf.db_email_server1_host))

	create_email=False
	try:
		if conf.db_email_server2_passwd is not None:
			create_email=True
	except:
		log.add(u"NOTICE: conf.db_email_server2_passwd is not defined - skip add email to server2")

	if create_email:
		num_op+=1
		status=email_db.add_user_to_exim_db(db_host=conf.db_email_server2_host, db_name=conf.db_email_server2_name, db_user=conf.db_email_server2_user, db_passwd=conf.db_email_server2_passwd, email_prefix=email_prefix, email_domain=conf.email_server2_domain, email_passwd=passwd, email_descr=fio)
		if status == STATUS_SUCCESS:
			log.add(u"SUCCESS add email to server: %s, %s" % (conf.db_email_server2_host, "%s@%s" % (email_prefix,conf.email_server2_domain)))
			print("""<p>УСПЕШНО заведён ящик %s@%s на сервере %s</p>""" % (email_prefix,conf.email_server2_domain,conf.db_email_server2_host))
			num_success_op+=1
		elif status == STATUS_USER_EXIST:
			log.add(u"ERROR USER EXIST  - add email to server: %s, %s failed - mailbox exist!" % (conf.db_email_server2_host, "%s@%s" % (email_prefix,conf.email_server2_domain)))
			print("""<p>ОШИБКА заведения ящика %s@%s на сервере %s - ящик УЖЕ СУЩЕСТВУЕТ</p>""" % (email_prefix,conf.email_server2_domain,conf.db_email_server2_host))
		else:
			log.add(u"ERROR add email to server: %s, %s" % (conf.db_email_server2_host, "%s@%s" % (email_prefix,conf.email_server2_domain)))
			print("""<p>ОШИБКА заведения ящика %s@%s на сервере %s</p>""" % (email_prefix,conf.email_server2_domain,conf.db_email_server2_host))

	#======================= Добавляем пользователя в базу: ====================
	# добавляем, только если хоть что-то получилось на предыдущем этапе:
	if num_success_op!=0:
		num_op+=1
		status = ad_user_db.add_ad_user(\
				name=user["name"], \
				familiya=user["familiya"],\
				otchestvo=user["otchestvo"], \
				login=user["login"],\
				old_login="",\
				passwd=user["passwd"], \
				drsk_email=user["email_server1"],\
				drsk_email_passwd=user["passwd"],\
				rsprim_email=user["email_server2"],\
				rsprim_email_passwd=user["passwd"],\
				hostname="",\
				ip="",\
				os="",\
				os_version="",\
				patches="",\
				doljnost=user["description"],\
				add_user_name=web_user_name,\
				add_ip=web_user_addr)
		if status == STATUS_SUCCESS:
			print("""<p>УСПЕШНО добавили пользователя '%s' в базу пользователей</p>""" % user["login"].encode('utf8'))
			log.add(u"""SUCCESS - добавили пользователя '%s' в базу пользователей""" %  user["login"].encode('utf8'))
			num_success_op+=1
		elif status == STATUS_USER_EXIST:
			print("""<p>ОШИБКА добавления записи о пользователе в базу данных (postgres) пользователей - ПОЛЬЗОВАЕЛЬ с таким ящиком rsprim.ru (%s) УЖЕ СУЩЕСТВУЕТ</p>""" % user["email_server2"])
			log.add(u"""ERROR - ошибка добавления записи пользователя '%s' базу пользоватлей""" % user["login"].encode('utf8'))
		else:
			print("""<p>ОШИБКА добавления записи о пользователе '%s' в базу данных (postgres) пользователей - обратитесь к системному администратору</p>""" % user["login"].encode('utf8'))
			log.add(u"""ERROR - ошибка добавления записи пользователя '%s' базу пользоватлей""" % user["login"].encode('utf8'))

	user["num_op"]=num_op
	user["num_success_op"]=num_success_op
	
	#========================  Сообщаем в лог полную информацию: =======================
	if num_success_op!=0:
		log.add(u"SUCCESS create user: (%(user_familia)s, %(user_name)s, %(user_otchestvo)s, %(user_description)s),\
login: %(login)s, passwd: '%(passwd)s', email_server1: %(email_server1)s, email_server2: %(email_server2)s, успешно выполненно задач: %(num_op)d из %(num_success_op)d"
		% {
		"user_familia":user_familia,
		"user_name":user_name,
		"user_otchestvo":user_otchestvo,
		"user_description":user_description,
		"login":user["login"],
		"passwd":user["passwd"],
		"email_server1":user["email_server1"],
		"email_server2":user["email_server2"],
		"num_op":num_op,
		"num_success_op":num_success_op
		})
	else:
		log.add(u"""Нет успешно выполненных операций при заведении пользователя '%s'""" %  user["login"])

	if num_success_op==0:
		return False
	else:
		return True


def CreateADUser(username, password, name, familiya, otchestvo, description, company, acl_groups,domain=conf.domain, employee_num="1",base_dn=conf.base_user_dn,group_acl_base=conf.group_acl_base):
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
		return STATUS_USER_EXIST

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
	# Наименование в списке просмотра пользователей через виндовый интерфейс:
	user_attrs['Name'] = familiya + ' ' + name + ' ' + otchestvo
	user_attrs['description'] = description
	user_attrs['company'] = company
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
		log.add(u"Error adding new user: %s" % error_message)
		return STATUS_INTERNAL_ERROR

	# Add the password
	try:
		ldap_connection.modify_s(user_dn, add_pass)
	except ldap.LDAPError, error_message:
		log.add(u"Error setting password: %s" % error_message)
		return STATUS_INTERNAL_ERROR

	# Change the account back to enabled
	try:
		ldap_connection.modify_s(user_dn, mod_acct)
	except ldap.LDAPError, error_message:
		log.add(u"Error enabling user: %s" % error_message)
		return STATUS_INTERNAL_ERROR

	# Add user to their primary group
	for acl_group in acl_groups:
		GROUP_DN="CN="+acl_group+","+ group_acl_base
		try:
			ldap_connection.modify_s(GROUP_DN, add_member)
		except ldap.LDAPError, error_message:
			log.add(u"Error adding user to group: %s" % error_message)
			return STATUS_INTERNAL_ERROR

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
	return STATUS_SUCCESS

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
	r2e[u"Й"]="Y"
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
	r2e[u"Щ"]="Sch"
	r2e[u"Ъ"]="-"
	r2e[u"Ы"]="Y"
	r2e[u"Ь"]="-"
	r2e[u"Э"]="E"
	r2e[u"Ю"]="Yu"
	r2e[u"Я"]="Ya"
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
	r2e[u"й"]="y"
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
	r2e[u"щ"]="sch"
	r2e[u"ъ"]="-"
	r2e[u"ы"]="y"
	r2e[u"ь"]="-"
	r2e[u"э"]="e"
	r2e[u"ю"]="yu"
	r2e[u"я"]="ya"

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
	user_addr="DEBUG - empty"
	ou_name = u"filial1"
else:
	form = cgi.FieldStorage()

	web_user_agent=os.getenv("HTTP_USER_AGENT")
	web_user_addr=os.getenv("REMOTE_ADDR")
	web_user_host=os.getenv("REMOTE_HOST")
	web_user_name=os.getenv('AUTHENTICATE_SAMACCOUNTNAME')

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
	ou_name = u"%s" % cgi.escape(form['ou_name'].value.decode('utf8'))
log.add(u"try create user: %s, %s, %s, %s" % (user_familia, user_name, user_otchestvo, user_description) )

# Обрабатываем ФИО - добавляем пользователя и выводим на экран результат:
user={}

if ou_name not in conf.ou:
	log.add(u"ERROR configuring - selected ou_name not in ou in config. selected ou_name val='%s'" % ou_name )
	sys.exit(1)

if create_drsk_user(user_familia,user_name,user_otchestvo,user_description,conf.ou[ou_name],user) is False:
	log.add(u"ERROR create user: %s, %s, %s, %s" % (user_familia, user_name, user_otchestvo, user_description) )
	print("<h1>Внутренняя ошибка!</h1>")
	print("</body></html>")
	sys.exit(1)
else:
	# Всё хорошо, печатаем результат:
	print("""<h1>Результат:</h1>""")
	print("""<p>Выполнено %d из %d задач</p>""" % (user["num_success_op"], user["num_op"]))
	print("""<h2>Успешно создан пользователь:</h2>""")
	print("""<h2>Имя:</h2>
	<p>%s</p>""" % user["fio"].encode('utf8'))
	print("""<h2>Логин:</h2>
	<p>%s</p>""" % user["login"].encode('utf8'))
	print("""<h2>Пароль:</h2>
	<p>%s</p>""" % user["passwd"].encode('utf8'))
	print("""<h2>Префикс почты:</h2>
	<p>%s</p>""" % user["email_prefix"].encode('utf8'))
	print("""<h2>Почтовый ящик1:</h2>
	<p>%s</p>""" % user["email_server1"].encode('utf8'))
	print("""<h2>Почтовый ящик2:</h2>
	<p>%s</p>""" % user["email_server2"].encode('utf8'))
	print("</body></html>")

	sys.exit(0)
