#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cgi
import os
import ldap_info as ad
import logger as log
import user_ad_postgres_db as ad_user_db
import config as conf
import user_phone_from_site

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

<style type="text/css">
tr:nth-child(even) {background: #DDD}
tr:nth-child(odd) {background: #FFF}
tr	{
	text-align:center;
	font-size: 0.835vw; //around 14px at 1920px
}
#cnt {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}	
#username {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
#acc {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
#pwd {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
#desc {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
#acc_drsk_email {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
#pwd_drsk_email {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
#acc_rsprim_email {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
#pwd_rsprim_email {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
#acc_status {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
#hostname {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
#cellphone {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
#position {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
#department {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
#host_ip {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
#host_os {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
#host_os_ver {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
#patches {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
#creator_ip {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
#created_time {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
#creator_who {
	border: 1px solid #8da1b5;
	font-family: Tahoma;
	color: #4f4f4f;
}
   .banned {
    color: red; /* Красный цвет выделения */
   }
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
users_phones=user_phone_from_site.get_users_phones_from_site()


print("""
    <TABLE BORDER>
    <TR>    
        <TH COLSPAN=22>Список пользователей домена</TH>
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
        <TH COLSPAN=1>Телефон</TH>
        <TH COLSPAN=1>Должность</TH>
        <TH COLSPAN=1>Отдел</TH>
        <TH COLSPAN=1>IP хоста польз.</TH>
        <TH COLSPAN=1>ОС</TH>
        <TH COLSPAN=1>Версия ОС</TH>
        <TH COLSPAN=1>Патчи</TH>
        <TH COLSPAN=1>С какого IP заведена</TH>
        <TH COLSPAN=1>Когда заведена</TH>
        <TH COLSPAN=1>Кто заводил</TH>
    </TR>
    """)

index=1
for account_name in users:
  user=users[account_name]
  fio=user["full_name"]
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

  # в разных базах - разный email:
  email_differ = False

  description="-"
  passwd="-"
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
  phone="-"
  job="-"
  department="-"

  if "description" in user:
    description=user["description"]
  
  if account_name in users_from_db:
    passwd=users_from_db[account_name]["passwd"]
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
#ip=users_from_db[account_name]["ip"]
    fio=users_from_db[account_name]["fio"]
    users_from_db[account_name]["show"]=True

  for comp_name in comps:
    if "description" in comps[comp_name]:
      if fio in comps[comp_name]["description"]:
        hostname=comps[comp_name]["name"]
  if fio in users_phones:
    phone=users_phones[fio]["phone"]
    job=users_phones[fio]["job"]
    department=users_phones[fio]["department"]
    if users_phones[fio]["email"] != "":
      if drsk_email != users_phones[fio]["email"]:
        # почта в приоритете с сайта:
        log.add("1c != userdb: '%s' != '%s'"%(users_phones[fio]["email"],drsk_email))
        drsk_email=users_phones[fio]["email"]
        email_differ = True

  # почта из AD:
  if "mail" in user:
    if user["mail"] != drsk_email:
      email_differ = True
      log.add("ad != 1c: '%s' != '%s'"%(user["mail"],drsk_email))

  if description == "":
    description="-"
  if passwd == "":
    passwd="-"
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
  if phone == "":
    phone="-"
  if job == "":
    job="-"
  if department == "":
    department="-"

  if email_differ:
    drsk_email = """<span class="banned">%s</span>""" % drsk_email

  print("""<TR>
     <TD id="cnt">%(index)d</TD>
     <TD id="username">%(full_name)s</TD>
     <TD id="acc">%(account_name)s</TD>
     <TD id="pwd">%(passwd)s</TD>
     <TD id="desc">%(description)s</TD>
     <TD id="acc_drsk_email">%(drsk_email)s</TD>
     <TD id="pwd_drsk_email">%(drsk_email_passwd)s</TD>
     <TD id="acc_rsprim_email">%(rsprim_email)s</TD>
     <TD id="pwd_rsprim_email">%(rsprim_email_passwd)s</TD>
     <TD id="acc_status">%(status)s</TD>
     <TD id="hostname">%(hostname)s</TD>
     <TD id="cellphone">%(phone)s</TD>
     <TD id="position">%(job)s</TD>
     <TD id="department">%(department)s</TD>
     <TD id="host_ip">%(ip)s</TD>
     <TD id="host_os">%(os)s</TD>
     <TD id="host_os_ver">%(os_version)s</TD>
     <TD id="patches">%(patches)s</TD>
     <TD id="creator_ip">%(add_ip)s</TD>
     <TD id="created_time">%(add_time)s</TD>
     <TD id="creator_who">%(add_user_name)s</TD>
     </TR>""" % {\
     "index":index, \
     "full_name":fio,\
     "description":description,\
     "account_name":user["account_name"],\
     "status":html_status,\
     "passwd":passwd,\
     "drsk_email":drsk_email,\
     "drsk_email_passwd":drsk_email_passwd,\
     "rsprim_email":rsprim_email,\
     "rsprim_email_passwd":rsprim_email_passwd,\
     "hostname":hostname,\
     "phone":phone,\
     "job":job,\
     "department":department,\
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
<br>
<br>
<br>
<br>
<br>
<br>
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
        <TH COLSPAN=1>Телефон</TH>
        <TH COLSPAN=1>Должность</TH>
        <TH COLSPAN=1>Отдел</TH>
        <TH COLSPAN=1>IP хоста польз.</TH>
        <TH COLSPAN=1>ОС</TH>
        <TH COLSPAN=1>Версия ОС</TH>
        <TH COLSPAN=1>Патчи</TH>
        <TH COLSPAN=1>С какого IP заведена</TH>
        <TH COLSPAN=1>Когда заведена</TH>
        <TH COLSPAN=1>Кто заводил</TH>
    </TR>
    """)

# сортировка:
users_svc=[]
users_no_svc=[]
users_sorted=[]
for fio in users_from_db_fio:
  login=users_from_db_fio[fio]["login"]
  if "svc_" in login.lower():
    users_svc.append(fio)
  else:
    users_no_svc.append(fio)


for fio in users_svc:
  users_sorted.append(fio)
for fio in users_no_svc:
  users_sorted.append(fio)

index=1
#for fio in users_from_db_fio:
for fio in users_sorted:
  user=users_from_db_fio[fio]
  status="-"
  description="-"
  passwd="-"
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
  phone="-"
  job="-"
  department="-"

  # Показываем, если нет в домене:
  if user["login"] in users:
    continue

  passwd=user["passwd"]
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

  if fio in users_phones:
    phone=users_phones[fio]["phone"]
    job=users_phones[fio]["job"]
    department=users_phones[fio]["department"]

  if account_name == "":
    account_name="-"
  if description == "":
    description="-"
  if passwd == "":
    passwd="-"
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
  if phone == "":
    phone="-"
  if job == "":
    job="-"
  if department == "":
    department="-"

  html_status="""<span class="banned">%s</span>""" % "Не заведён в домене"

  print("""<TR>
     <TD id="cnt">%(index)d</TD>
     <TD id="username">%(full_name)s</TD>
     <TD id="acc">%(account_name)s</TD>
     <TD id="pwd">%(passwd)s</TD>
     <TD id="desc">%(description)s</TD>
     <TD id="acc_drsk_email">%(drsk_email)s</TD>
     <TD id="pwd_drsk_email">%(drsk_email_passwd)s</TD>
     <TD id="acc_rsprim_email">%(rsprim_email)s</TD>
     <TD id="pwd_rsprim_email">%(rsprim_email_passwd)s</TD>
     <TD id="acc_status">%(status)s</TD>
     <TD id="hostname">%(hostname)s</TD>
     <TD id="cellphone">%(phone)s</TD>
     <TD id="position">%(job)s</TD>
     <TD id="department">%(department)s</TD>
     <TD id="host_ip">%(ip)s</TD>
     <TD id="host_os">%(os)s</TD>
     <TD id="host_os_ver">%(os_version)s</TD>
     <TD id="patches">%(patches)s</TD>
     <TD id="creator_ip">%(add_ip)s</TD>
     <TD id="created_time">%(add_time)s</TD>
     <TD id="creator_who">%(add_user_name)s</TD>
     </TR>""" % {\
     "index":index, \
     "full_name":fio,\
     "description":description,\
     "account_name":account_name,\
     "status":html_status,\
     "passwd":passwd,\
     "drsk_email":drsk_email,\
     "drsk_email_passwd":drsk_email_passwd,\
     "rsprim_email":rsprim_email,\
     "rsprim_email_passwd":rsprim_email_passwd,\
     "hostname":hostname,\
     "phone":phone,\
     "job":job,\
     "department":department,\
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
