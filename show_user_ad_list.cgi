#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cgi
import os
import ldap_info as ad
import logger as log
import user_ad_postgres_db as ad_user_db
import config as conf

web_user_agent=os.getenv("HTTP_USER_AGENT")
web_user_addr=os.getenv("REMOTE_ADDR")
web_user_host=os.getenv("REMOTE_HOST")
web_user_name=os.getenv('AUTHENTICATE_SAMACCOUNTNAME')

log.add("view ad list from: IP: %(web_user_addr)s, auth_name: %(web_user_name)s," % {"web_user_addr":web_user_addr, "web_user_name":web_user_name} )

#print "Content-Type: text/html\n\n"; 
print("""
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<HTML>
<HEAD>
<META HTTP-EQUIV="CONTENT-TYPE" CONTENT="text/html; charset=utf-8">
<TITLE>Список пользователей домена DRSK</TITLE>
<META NAME="GENERATOR" CONTENT="OpenOffice.org 3.1  (Linux)">
<META NAME="AUTHOR" CONTENT="Сергей Семёнов">
<META NAME="CREATED" CONTENT="20100319;10431100">
<META NAME="CHANGEDBY" CONTENT="Сергей Семёнов">
<META NAME="CHANGED" CONTENT="20100319;10441400">
<STYLE TYPE="text/css">
<!--
@page { size: 21cm 29.7cm; margin: 2cm }
P { margin-bottom: 0.21cm }
-->
</STYLE>

<style>
   .normal {
   }
</style>
<style>
   .banned {
    color: red; /* Красный цвет выделения */
   }
</style>
<style>
   .selected_node {
    color: green; /* Зелёный цвет выделения */
	background: #D9FFAD;
	font-size: 150%;
   }
</style>

</HEAD>
<BODY LANG="ru-RU" LINK="#000080" VLINK="#800000" DIR="LTR">
""")

l=ad.init()
users=ad.get_users(l)
comps=ad.get_computers(l)
users_from_db=ad_user_db.get_ad_user_list_by_login()
users_from_db_fio=ad_user_db.get_ad_user_list_by_fio()


print("""
		<TABLE BORDER>
		<TR>    
				<TH COLSPAN=19>Список пользователей домена</TH>
		</TR>
		<TR>
				<TH COLSPAN=1>№</TH>
				<TH COLSPAN=1>Полное имя пользователя</TH>
				<TH COLSPAN=1>Логин</TH>
				<TH COLSPAN=1>Пароль</TH>
				<TH COLSPAN=1>Описание</TH>
				<TH COLSPAN=1>Почта ДРСК</TH>
				<TH COLSPAN=1>Пароль почты ДРСК</TH>
				<TH COLSPAN=1>Почта rsprim</TH>
				<TH COLSPAN=1>Пароль почты rsprim</TH>
				<TH COLSPAN=1>Статус учётки</TH>
				<TH COLSPAN=1>Имя хоста польз.</TH>
				<TH COLSPAN=1>IP хоста польз.</TH>
				<TH COLSPAN=1>ОС</TH>
				<TH COLSPAN=1>Версия ОС</TH>
				<TH COLSPAN=1>Патчи</TH>
				<TH COLSPAN=1>Старый логин</TH>
				<TH COLSPAN=1>С какого IP заведена</TH>
				<TH COLSPAN=1>Когда заведена</TH>
				<TH COLSPAN=1>Кто заводил</TH>
		</TR>
		""")

index=1
for account_name in users:
	user=users[account_name]
	status=""
	if user["attr"] & ad.ACCOUNTDISABLE:
		status=status+"Заблокирован, "
	if user["attr"] & ad.DONT_EXPIRE_PASSWORD:
		status=status+"Не требующий замены,"
	if user["attr"] & ad.PASSWORD_EXPIRED:
		status=status+"Закончился, "
	if user["attr"] & ad.NORMAL_ACCOUNT:
		status=status+"Нормальный"

	if status != "Нормальный":
		html_status="""<span class="banned">%s</span>""" % status
	else:
		html_status="""<span class="normal">%s</span>""" % status

	description="-"
	passwd="-"
	old_login="-"
	drsk_email="-"
	drsk_email_passwd="-"
	rsprim_email="-"
	rsprim_email_passwd="-"
	os="-"
	os_version="-"
	patches="-"
	add_time="-"
	add_ip="-"
	add_user_name="-"
	hostname="-"
	ip="-"

	if "description" in user:
		description=user["description"]
	
	if account_name in users_from_db:
		passwd=users_from_db[account_name]["passwd"]
		old_login=users_from_db[account_name]["old_login"]
		drsk_email=users_from_db[account_name]["drsk_email"]
		drsk_email_passwd=users_from_db[account_name]["drsk_email_passwd"]
		rsprim_email=users_from_db[account_name]["rsprim_email"]
		rsprim_email_passwd=users_from_db[account_name]["rsprim_email_passwd"]
		os=users_from_db[account_name]["os"]
		os_version=users_from_db[account_name]["os_version"]
		patches=users_from_db[account_name]["patches"]
		add_time=users_from_db[account_name]["add_time"]
		add_ip=users_from_db[account_name]["add_ip"]
		add_user_name=users_from_db[account_name]["add_user_name"]
		ip=users_from_db[account_name]["ip"]
		hostname=users_from_db[account_name]["hostname"]
		users_from_db[account_name]["show"]=True

	if description == "":
		description="-"
	if passwd == "":
		passwd="-"
	if old_login == "":
		old_login="-"
	if drsk_email == "":
		drsk_email="-"
	if drsk_email_passwd == "":
		drsk_email_passwd="-"
	if rsprim_email == "":
		rsprim_email="-"
	if rsprim_email_passwd == "":
		rsprim_email_passwd="-"
	if os == "":
		os="-"
	if os_version == "":
		os_version="-"
	if patches == "":
		patches="-"
	if add_time == "":
		add_time="-"
	if add_ip == "":
		add_ip="-"
	if add_user_name == "":
		add_user_name="-"
	if hostname == "":
		hostname="-"
	if ip == "":
		ip="-"

	print("""<TR>
		 <TD>%(index)d</TD>
		 <TD>%(full_name)s</TD>
		 <TD>%(account_name)s</TD>
		 <TD>%(passwd)s</TD>
		 <TD>%(description)s</TD>
		 <TD>%(drsk_email)s</TD>
		 <TD>%(drsk_email_passwd)s</TD>
		 <TD>%(rsprim_email)s</TD>
		 <TD>%(rsprim_email_passwd)s</TD>
		 <TD>%(status)s</TD>
		 <TD>%(hostname)s</TD>
		 <TD>%(ip)s</TD>
		 <TD>%(os)s</TD>
		 <TD>%(os_version)s</TD>
		 <TD>%(patches)s</TD>
		 <TD>%(old_login)s</TD>
		 <TD>%(add_ip)s</TD>
		 <TD>%(add_time)s</TD>
		 <TD>%(add_user_name)s</TD>
		 </TR>""" % {\
		 "index":index, \
		 "full_name":user["full_name"],\
		 "description":description,\
		 "account_name":user["account_name"],\
		 "status":html_status,\
		 "passwd":passwd,\
		 "old_login":old_login,\
		 "drsk_email":drsk_email,\
		 "drsk_email_passwd":drsk_email_passwd,\
		 "rsprim_email":rsprim_email,\
		 "rsprim_email_passwd":rsprim_email_passwd,\
		 "hostname":hostname,\
		 "ip":ip,\
		 "os":os,\
		 "os_version":os_version,\
		 "patches":patches,\
		 "add_time":add_time,\
		 "add_ip":add_ip,\
		 "add_user_name":add_user_name\
		 })
	index+=1


print("</TABLE>")


print("""
		<TABLE BORDER>
		<TR>    
				<TH COLSPAN=19>Список пользователей из базы данных, не заведённых в домене</TH>
		</TR>
		<TR>
				<TH COLSPAN=1>№</TH>
				<TH COLSPAN=1>Полное имя пользователя</TH>
				<TH COLSPAN=1>Логин</TH>
				<TH COLSPAN=1>Пароль</TH>
				<TH COLSPAN=1>Описание</TH>
				<TH COLSPAN=1>Почта ДРСК</TH>
				<TH COLSPAN=1>Пароль почты ДРСК</TH>
				<TH COLSPAN=1>Почта rsprim</TH>
				<TH COLSPAN=1>Пароль почты rsprim</TH>
				<TH COLSPAN=1>Статус учётки</TH>
				<TH COLSPAN=1>Имя хоста польз.</TH>
				<TH COLSPAN=1>IP хоста польз.</TH>
				<TH COLSPAN=1>ОС</TH>
				<TH COLSPAN=1>Версия ОС</TH>
				<TH COLSPAN=1>Патчи</TH>
				<TH COLSPAN=1>Старый логин</TH>
				<TH COLSPAN=1>С какого IP заведена</TH>
				<TH COLSPAN=1>Когда заведена</TH>
				<TH COLSPAN=1>Кто заводил</TH>
		</TR>
		""")

index=1
for fio in users_from_db_fio:
	user=users_from_db_fio[fio]
	status="-"
	description="-"
	passwd="-"
	old_login="-"
	drsk_email="-"
	drsk_email_passwd="-"
	rsprim_email="-"
	rsprim_email_passwd="-"
	os="-"
	os_version="-"
	patches="-"
	add_time="-"
	add_ip="-"
	add_user_name="-"
	hostname="-"
	ip="-"

	# Показываем, если нет в домене:
	if user["login"] in users:
		continue

	passwd=user["passwd"]
	old_login=user["old_login"]
	drsk_email=user["drsk_email"]
	drsk_email_passwd=user["drsk_email_passwd"]
	rsprim_email=user["rsprim_email"]
	rsprim_email_passwd=user["rsprim_email_passwd"]
	os=user["os"]
	os_version=user["os_version"]
	patches=user["patches"]
	add_time=user["add_time"]
	add_ip=user["add_ip"]
	add_user_name=user["add_user_name"]
	ip=user["ip"]
	hostname=user["hostname"]
	user["show"]=True
	description=user["doljnost"]
	account_name=user["login"]

	if account_name == "":
		account_name="-"
	if description == "":
		description="-"
	if passwd == "":
		passwd="-"
	if old_login == "":
		old_login="-"
	if drsk_email == "":
		drsk_email="-"
	if drsk_email_passwd == "":
		drsk_email_passwd="-"
	if rsprim_email == "":
		rsprim_email="-"
	if rsprim_email_passwd == "":
		rsprim_email_passwd="-"
	if os == "":
		os="-"
	if os_version == "":
		os_version="-"
	if patches == "":
		patches="-"
	if add_time == "":
		add_time="-"
	if add_ip == "":
		add_ip="-"
	if add_user_name == "":
		add_user_name="-"
	if hostname == "":
		hostname="-"
	if ip == "":
		ip="-"

	print("""<TR>
		 <TD>%(index)d</TD>
		 <TD>%(full_name)s</TD>
		 <TD>%(account_name)s</TD>
		 <TD>%(passwd)s</TD>
		 <TD>%(description)s</TD>
		 <TD>%(drsk_email)s</TD>
		 <TD>%(drsk_email_passwd)s</TD>
		 <TD>%(rsprim_email)s</TD>
		 <TD>%(rsprim_email_passwd)s</TD>
		 <TD>%(status)s</TD>
		 <TD>%(hostname)s</TD>
		 <TD>%(ip)s</TD>
		 <TD>%(os)s</TD>
		 <TD>%(os_version)s</TD>
		 <TD>%(patches)s</TD>
		 <TD>%(old_login)s</TD>
		 <TD>%(add_ip)s</TD>
		 <TD>%(add_time)s</TD>
		 <TD>%(add_user_name)s</TD>
		 </TR>""" % {\
		 "index":index, \
		 "full_name":fio,\
		 "description":description,\
		 "account_name":account_name,\
		 "status":html_status,\
		 "passwd":passwd,\
		 "old_login":old_login,\
		 "drsk_email":drsk_email,\
		 "drsk_email_passwd":drsk_email_passwd,\
		 "rsprim_email":rsprim_email,\
		 "rsprim_email_passwd":rsprim_email_passwd,\
		 "hostname":hostname,\
		 "ip":ip,\
		 "os":os,\
		 "os_version":os_version,\
		 "patches":patches,\
		 "add_time":add_time,\
		 "add_ip":add_ip,\
		 "add_user_name":add_user_name\
		 })
	index+=1


print("</TABLE>")



print("""
</body>
</html>
""")


# Some flags for userAccountControl property
SCRIPT = 1
ACCOUNTDISABLE = 2
HOMEDIR_REQUIRED = 8
PASSWD_NOTREQD = 32
NORMAL_ACCOUNT = 512
DONT_EXPIRE_PASSWORD = 65536
TRUSTED_FOR_DELEGATION = 524288
PASSWORD_EXPIRED = 8388608
