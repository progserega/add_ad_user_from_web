#!/usr/bin/env python3
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
import logging
from logging import handlers
import user_ad_postgres_db as ad_user_db
import add_to_email_db as email_db
import sendemail
import traceback

log = None
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

def get_exception_traceback_descr(e):
  if hasattr(e, '__traceback__'):
    tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
    result=""
    for msg in tb_str:
      result+=msg
    return result
  else:
    return e

def create_drsk_user(user_familia,user_name,user_otchestvo,description, ou_name, user,web_user_name,web_user_addr):
  global log
  num_op=0
  num_success_op=0
  full_status={}
  fam=user_familia
  name=user_name
  otch=user_otchestvo
  fio=fam + " " + name + " " + otch
  login=rus2en(fam.lower()) + "_" + rus2en(name.lower())[0] + rus2en(otch.lower())[0]  
  email_prefix=rus2en(fam.lower()) + "-" + rus2en(name.lower())[0] + rus2en(otch.lower())[0]  
  email_server1=email_prefix+"@"+conf.email_server1_domain
  email_server2=email_prefix+"@"+conf.email_server2_domain
  for i in range(1,40):
    passwd=get_passwd()
    if re.search('[1lIO0]',passwd) == None:
      break

  log.debug(u"ФИО: %s" % fio )
  log.debug(u"Логин: %s" % login)
  log.debug(u"Пароль: '%s'" % passwd)
  log.debug(u"Почта префикс: %s" % email_prefix)
  log.debug(u"Почта ДРСК: %s" % email_server1)
  log.debug(u"Почта rsprim: %s" % email_server2)

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
  status=CreateADUser(login, passwd, name, fam, otch, description, email_server1, conf.default_groups[ou_name]["name"], groups=conf.default_groups[ou_name]["groups"],domain=conf.domain, employee_num="1",base_dn=conf.base_user_dn,group_acl_base=conf.group_acl_base, group_rbl_base=conf.group_rbl_base)
  if status == STATUS_SUCCESS:
    num_success_op+=1
    print("""<p><span class='success'>УСПЕШНО</span> заведён пользователь %s в домене""" % login)
    log.info("""SUCCESS - успешно заведенна учётная запись '%s' в домене""" % login) 
    full_status["создание пользователя в домене"]="успешно"
  elif status == STATUS_USER_EXIST:
    print("""<p><span class='error'>ОШИБКА</span> заведения учётной записи '%s' в домене - пользователь УЖЕ СУЩЕСТВУЕТ</p>""" % login) 
    log.error("""ERROR USER EXIST - ошибка заведения учётной записи '%s' в домене - пользователь УЖЕ СУЩЕСТВУЕТ""" % login) 
    full_status["создание пользователя в домене"]="ошибка - этот пользователь в домене уже существует"
  else:
    print("""<p><span class='error'>ОШИБКА</span> заведения учётной записи '%s' в домене</p>""" % login) 
    log.error(u"""ERROR - ошибка заведения учётной записи '%s' в домене""" % login) 
    full_status["создание пользователя в домене"]="ошибка - внутренняя ошибка скрипта при создании пользователя"

  #=============================  Добавляем в почтовые сервера: ========================
  create_email=False
  try:
    if conf.db_email_server1_passwd is not None:
      create_email=True
  except:
    log.info("NOTICE: conf.db_email_server1_passwd is not defined - skip add email to server1")
  if create_email:
    num_op+=1
    status=email_db.add_user_to_exim_db(log,db_host=conf.db_email_server1_host, db_name=conf.db_email_server1_name, db_user=conf.db_email_server1_user, db_passwd=conf.db_email_server1_passwd, email_prefix=email_prefix, email_domain=conf.email_server1_domain, email_passwd=passwd, email_descr=fio)
    if status == STATUS_SUCCESS:
      log.info("SUCCESS add email to server: %s, %s" % (conf.db_email_server1_host, "%s@%s" % (email_prefix,conf.email_server1_domain)))
      print("""<p><span class='success'>УСПЕШНО</span> заведён ящик %s@%s на сервере %s</p>""" % (email_prefix,conf.email_server1_domain,conf.db_email_server1_host))
      num_success_op+=1
      full_status["заведение почты на основном (prim.drsk.ru) сервере"]="успешно"
    elif status == STATUS_USER_EXIST:
      log.error("ERROR USER EXIST  - add email to server: %s, %s failed - mailbox exist!" % (conf.db_email_server1_host, "%s@%s" % (email_prefix,conf.email_server1_domain)))
      print("""<p><span class='error'>ОШИБКА</span> заведения ящика %s@%s на сервере %s - ящик УЖЕ СУЩЕСТВУЕТ</p>""" % (email_prefix,conf.email_server1_domain,conf.db_email_server1_host))
      full_status["заведение почты на основном (prim.drsk.ru) сервере"]="ошибка - такой пользователь уже существует"
    else:
      log.error("ERROR add email to server: %s, %s" % (conf.db_email_server1_host, "%s@%s" % (email_prefix,conf.email_server1_domain)))
      print("""<p><span class='error'>ОШИБКА</span> заведения ящика %s@%s на сервере %s</p>""" % (email_prefix,conf.email_server1_domain,conf.db_email_server1_host))
      full_status["заведение почты на основном (prim.drsk.ru) сервере"]="ошибка - внутренняя ошибка скрипта"

  create_email=False
  try:
    if conf.db_email_server2_passwd is not None:
      create_email=True
  except:
    log.info("NOTICE: conf.db_email_server2_passwd is not defined - skip add email to server2")

  if create_email:
    num_op+=1
    status=email_db.add_user_to_exim_db(log,db_host=conf.db_email_server2_host, db_name=conf.db_email_server2_name, db_user=conf.db_email_server2_user, db_passwd=conf.db_email_server2_passwd, email_prefix=email_prefix, email_domain=conf.email_server2_domain, email_passwd=passwd, email_descr=fio)
    if status == STATUS_SUCCESS:
      log.info("SUCCESS add email to server: %s, %s" % (conf.db_email_server2_host, "%s@%s" % (email_prefix,conf.email_server2_domain)))
      print("""<p><span class='success'>УСПЕШНО</span> заведён ящик %s@%s на сервере %s</p>""" % (email_prefix,conf.email_server2_domain,conf.db_email_server2_host))
      full_status["заведение почты на резервном (rsprim.ru) сервере"]="успешно"
      num_success_op+=1
    elif status == STATUS_USER_EXIST:
      log.error("ERROR USER EXIST  - add email to server: %s, %s failed - mailbox exist!" % (conf.db_email_server2_host, "%s@%s" % (email_prefix,conf.email_server2_domain)))
      print("""<p><span class='error'>ОШИБКА</span> заведения ящика %s@%s на сервере %s - ящик УЖЕ СУЩЕСТВУЕТ</p>""" % (email_prefix,conf.email_server2_domain,conf.db_email_server2_host))
      full_status["заведение почты на резервном (rsprim.ru) сервере"]="ошибка - такой пользователь уже существует"
    else:
      log.error("ERROR add email to server: %s, %s" % (conf.db_email_server2_host, "%s@%s" % (email_prefix,conf.email_server2_domain)))
      print("""<p><span class='error'>ОШИБКА</span> заведения ящика %s@%s на сервере %s</p>""" % (email_prefix,conf.email_server2_domain,conf.db_email_server2_host))
      full_status["заведение почты на резервном (rsprim.ru) сервере"]="ошибка - внутренняя ошибка скрипта"

  #======================= Добавляем пользователя в базу: ====================
  # добавляем, только если хоть что-то получилось на предыдущем этапе:
  if num_success_op!=0:
    num_op+=1
    status = ad_user_db.add_ad_user(log,\
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
      print("""<p><span class='success'>УСПЕШНО</span> добавили пользователя '%s' в базу пользователей</p>""" % user["login"])
      log.info("""SUCCESS - добавили пользователя '%s' в базу пользователей""" %  user["login"])
      full_status["добавление пользователя в базу пользователей"]="успешно"
      num_success_op+=1
    elif status == STATUS_USER_EXIST:
      print("""<p><span class='error'>ОШИБКА</span> добавления записи о пользователе в базу данных (postgres) пользователей - ПОЛЬЗОВАЕЛЬ с таким ящиком rsprim.ru (%s) УЖЕ СУЩЕСТВУЕТ</p>""" % user["email_server2"])
      log.error("""ERROR - ошибка добавления записи пользователя '%s' базу пользоватлей""" % user["login"])
      full_status["добавление пользователя в базу пользователей"]="ошибка - такой пользователь уже существует"
    else:
      print("""<p><span class='error'>ОШИБКА</span> добавления записи о пользователе '%s' в базу данных (postgres) пользователей - обратитесь к системному администратору</p>""" % user["login"])
      log.error("""ERROR - ошибка добавления записи пользователя '%s' базу пользоватлей""" % user["login"])
      full_status["добавление пользователя в базу пользователей"]="ошибка - внутренняя ошибка скрипта"
  #===================== Отправляем по почте данные пользователя, но без пароля: =================
  if num_success_op!=0:
    mail_login=email_server1.split('@')[0]
    text="""Добрый день! 

Письмо сгенерировано автоматически. 

Администратор с логином '%(admin)s' завёл пользователя с IP-адрса: %(ip)s. 

Данные заведённого пользователя:
ФИО: %(fio)s
Логин: %(login)s
Описание пользователя: %(descr)s
Основная почта: %(email1)s
Дополнительная почта: %(email2)s

Почтовый логин (для заведения в почте): %(mail_login)s

Пароль можно получить по ссылке:
https://arm-sit.rs.int/index.php?AdUsersSearch[fio]=&AdUsersSearch[old_familiya]=&AdUsersSearch[login]=%(login)s&AdUsersSearch[passwd]=&AdUsersSearch[drsk_email]=&AdUsersSearch[rsprim_email]=&AdUsersSearch[add_time]=&AdUsersSearch[add_user_name]=&r=ad-users%%2Findex

Отчёт о проделанной работе:
""" % \
    {\
    "admin":web_user_name,\
      "ip":web_user_addr,\
      "fio":user["fio"],\
      "login":user["login"],\
      "mail_login":mail_login,\
      "descr":user["description"],\
      "email1":email_server1,\
      "email2":email_server2\
    }
    # Статусы выполненных действий:
    index=1
    for name in full_status:
      text=text + "%d"%index +") " + name + ": " + full_status[name] + "\n"
      index+=1
    text=text + "\nСпасибо за внимание!"

    subj="'%s' создал нового пользователя '%s' в системе" % (web_user_name,user["login"])
    for send_to in conf.send_report_to:
      num_op+=1
      if sendemail.sendmail(text=text, subj=subj,send_to=send_to,send_from=conf.send_report_from,isTls=False) == True:
        num_success_op+=1
        print("""<p><span class='success'>УСПЕШНО</span> отправил уведомление по почте пользователю: %s</p>""" % send_to)
        log.info("""SUCCESS - успешно отправил уведомление пользователю: '%s'""" % send_to)
      else:
        print("""<p><span class='error'>ОШИБКА</span> отправки уведомления по почте на %s</p>""" % send_to)
        log.error("""ERROR - ошибка отправки уведомления пользователю: '%s'""" % send_to)
        
  #=======================================================================
  user["num_op"]=num_op
  user["num_success_op"]=num_success_op
  
  #========================  Сообщаем в лог полную информацию: =======================
  if num_success_op!=0:
    log.info("SUCCESS create user: (%(user_familia)s, %(user_name)s, %(user_otchestvo)s, %(user_description)s),\
login: %(login)s, passwd: '%(passwd)s', email_server1: %(email_server1)s, email_server2: %(email_server2)s, успешно выполненно задач: %(num_op)d из %(num_success_op)d"
    % {
    "user_familia":user_familia,
    "user_name":user_name,
    "user_otchestvo":user_otchestvo,
    "user_description":description,
    "login":user["login"],
    "passwd":user["passwd"],
    "email_server1":user["email_server1"],
    "email_server2":user["email_server2"],
    "num_op":num_op,
    "num_success_op":num_success_op
    })
  else:
    log.error("""Нет успешно выполненных операций при заведении пользователя '%s'""" %  user["login"])

  if num_success_op==0:
    return False
  else:
    return True


def CreateADUser(username, password, name, familiya, otchestvo, description, email, company, groups,domain=conf.domain, employee_num="1",base_dn=conf.base_user_dn,group_acl_base=conf.group_acl_base, group_rbl_base=conf.group_rbl_base):
  #Create a new user account in Active Directory.
  try:
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
    except ldap.LDAPError as desc:
      log.error(desc)
      return None
    except Exception as e:
      log.error(get_exception_traceback_descr(e))
      return None

    # Check and see if user exists
    try:
      user_results = ldap_connection.search_s(base_dn, ldap.SCOPE_SUBTREE,
        '(&(sAMAccountName=' +
        username +
        ')(objectClass=person))',
        ['distinguishedName'])
    except ldap.LDAPError as desc:
      log.error("Error finding username: %s" % desc)
      return STATUS_INTERNAL_ERROR

    # Check the results
    if len(user_results) != 0:
      log.warning("User %s already exists in AD:" % username )
  #print "User", username, "already exists in AD:", \
      user_results[0][1]['distinguishedName'][0]
      return STATUS_USER_EXIST

    # Lets build our user: Disabled to start (514)
    user_dn = 'cn=' + fname + ' ' + lname + ',' + base_dn
    user_attrs = {}
    user_attrs['objectClass'] = \
    [b'top', b'person', b'organizationalPerson', b'user']
    user_attrs['cn'] = (fname + ' ' + lname).encode('utf8')
    #user_attrs['cn'] = (familiya + ' ' + name + ' ' + otchestvo).encode('utf8')
    user_attrs['userPrincipalName'] = (username + '@' + domain).encode('utf8')
    user_attrs['sAMAccountName'] = username.encode('utf8')
    user_attrs['givenName'] = fname.encode('utf8')
    user_attrs['sn'] = lname.encode('utf8')
    user_attrs['displayName'] = (familiya + ' ' + name + ' ' + otchestvo).encode('utf8')
    # Наименование в списке просмотра пользователей через виндовый интерфейс:
    user_attrs['name'] = (familiya + ' ' + name + ' ' + otchestvo).encode('utf8')
    user_attrs['description'] = description.encode('utf8')
    user_attrs['company'] = company.encode('utf8')
    #user_attrs['userAccountControl'] = '514'
    user_attrs['userAccountControl'] = ("%d" % (NORMAL_ACCOUNT + DONT_EXPIRE_PASSWORD + ACCOUNTDISABLE)).encode('utf8')
    #user_attrs['mail'] = username + '@host.com'
    user_attrs['employeeID'] = employee_num.encode('utf8')
    #user_attrs['homeDirectory'] = '\\\\server\\' + username
    #user_attrs['homeDrive'] = 'H:'
    #user_attrs['scriptPath'] = 'logon.vbs'
    user_ldif = modlist.addModlist(user_attrs)

    # Prep the password
    #unicode_pass = unicode('\"' + password + '\"', 'iso-8859-1')
    #password_value = unicode_pass.encode('utf-16-le')
    unicode_pass = '\"' + password + '\"'
    password_value = unicode_pass.encode('utf-16-le')
    #password_value = unicode_pass.getBytes("UTF-16LE")
    add_pass = [(ldap.MOD_REPLACE, 'unicodePwd', [password_value])]
    # 512 will set user account to enabled
    flags = NORMAL_ACCOUNT
    if conf.user_password_is_expired == False:
      flags += DONT_EXPIRE_PASSWORD
    mod_acct = [(ldap.MOD_REPLACE, 'userAccountControl', ("%d" % flags).encode('utf8') )]
    # New group membership
    add_member = [(ldap.MOD_ADD, 'member', user_dn.encode('utf8'))]
    #mod_pgid = [(ldap.MOD_REPLACE, 'primaryGroupID', GROUP_TOKEN)]
    # Delete the Domain Users group membership
    #del_member = [(ldap.MOD_DELETE, 'member', user_dn)]

    #unicode_email = unicode(email, 'iso-8859-1')
    #email_value = email.encode('utf-16-le')
    email_value = email.encode('utf8')
#    log.info("test: email=%s"%email)
#    log.info("encoded:")
#    log.info(email_value)
#    email_value = b'atest@mail.ru'
#    log.info("byte::")
#    log.info(email_value)
    #email_value = email.getBytes("UTF-16LE")
    mod_email = [(ldap.MOD_REPLACE, 'mail', [email_value])]

    # Add the new user account
    try:
      ldap_connection.add_s(user_dn, user_ldif)
    except ldap.LDAPError as desc:
      log.error("Error adding new user: %s" % desc)
      return STATUS_INTERNAL_ERROR

    # Add the password
    try:
      ldap_connection.modify_s(user_dn, add_pass)
    except ldap.LDAPError as error_message:
      log.error("Error setting password: %s" % error_message)
      return STATUS_INTERNAL_ERROR

    # Change the account back to enabled
    try:
      ldap_connection.modify_s(user_dn, mod_acct)
    except ldap.LDAPError as error_message:
      log.error("Error enabling user: %s" % error_message)
      return STATUS_INTERNAL_ERROR

    # mod the email:
    try:
      ldap_connection.modify_s(user_dn, mod_email)
    except ldap.LDAPError as error_message:
      log.error("Error modify email: %s" % error_message)
      return STATUS_INTERNAL_ERROR

    # Add user to their primary group
    for group in groups:
      if re.search("^rbl.*", group.lower()) is not None:
        GROUP_DN="CN="+group+","+ group_rbl_base
      elif re.search("^acl.*", group.lower()) is not None:
        GROUP_DN="CN="+group+","+ group_acl_base
      else:
        log.error(u"Error adding user to group: %s - group must begin from 'ACL' or 'RBL'! - skip this group" % group)
        continue
      try:
        ldap_connection.modify_s(GROUP_DN, add_member)
      except ldap.LDAPError as error_message:
        log.error("Error adding user to group: %s" % error_message)
        log.error("Error groups: %s" % GROUP_DN)

    

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
  except Exception as e:
    log.error(get_exception_traceback_descr(e))
    return STATUS_INTERNAL_ERROR

def get_passwd():
  try:
    t = subprocess.Popen(("pwgen","-s" ,"%d"%conf.password_lenght, "1"), stderr=subprocess.PIPE,stdout=subprocess.PIPE)
    ret_code=t.wait()
    t_stdout_list=t.stdout.readlines()
    return t_stdout_list[0].decode('utf8').strip('\n')
  except Exception as e:
    log.error(get_exception_traceback_descr(e))
    return None

def rus2en(string):
  try:
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
  except Exception as e:
    log.error(get_exception_traceback_descr(e))
    return None



# ========== main ==============
def main():
  try:
    if conf.allow_add_users != True:
      log.warning("configuration is block run adding users! Skip running! Exit!")
      return True

    if conf.console:
      user_familia = "Фамилия"
      user_name = "Имя"
      user_otchestvo = "Отчество"
      user_description = "(А - для сортировки) описание"
      user_addr="DEBUG - empty"
      ou_name = "filial"
      web_user_name="DEBUG script in console"
      web_user_agent="console"
      web_user_addr="127.0.0.1"
      web_user_host="localhost"
    else:
      form = cgi.FieldStorage()

      web_user_agent=os.getenv("HTTP_USER_AGENT")
      web_user_addr=os.getenv("REMOTE_ADDR")
      web_user_host=os.getenv("REMOTE_HOST")
      web_user_name=os.getenv('AUTHENTICATE_SAMACCOUNTNAME')
      if web_user_name is None:
        web_user_name=os.getenv('REMOTE_USER')

      print("""
      <html>
      <head>
      <meta http-equiv='Content-Type' content='text/html; charset=utf-8'>
      <title>Результат выполнения</title>

        <style>
        .password {
     /*   color: green;  Зелёный цвет выделения */
     /*   background: #D9FFAD; */
        font-size: 150%;
        /*font-family: courier-new;*/
        font-family: Andale Mono;
        }
        </style>

        <style>
        .info {
        color: green;  /* Зелёный цвет выделения */
        background: #D9FFAD; 
        font-size: 150%;
        /*font-family: courier-new;*/
        font-family: Andale Mono;
        }
        </style>

        <style>
        .success {
        background: green; 
        }
        </style>

        <style>
        .error {
        background: red; 
        }
        </style>

      </head>
      <body>
      """ )

      # Поле 'work_sites_regex' содержит не пустое значение:
      if 'user_familia' in form and 'user_name' in form and 'user_otchestvo' in form and 'user_description' in form:
        user_familia = "%s" % cgi.escape(form['user_familia'].value)
        user_name = "%s" % cgi.escape(form['user_name'].value)
        user_otchestvo = "%s" % cgi.escape(form['user_otchestvo'].value)
        user_description = "%s" % cgi.escape(form['user_description'].value)
      else:
        print("Необходимо заполнить все поля")
        print("</body></html>")
        return False
      ou_name = "%s" % cgi.escape(form['ou_name'].value)
    log.info("try create user: %s, %s, %s, %s" % (user_familia, user_name, user_otchestvo, user_description) )

    # Обрабатываем ФИО - добавляем пользователя и выводим на экран результат:
    user={}

    if create_drsk_user(user_familia,user_name,user_otchestvo,user_description,ou_name,user,web_user_name,web_user_addr) is False:
      log.error("ERROR create user: %s, %s, %s, %s" % (user_familia, user_name, user_otchestvo, user_description) )
      print("<h1>Внутренняя ошибка!</h1>")
      print("</body></html>")
      return False
    else:
      # Всё хорошо, печатаем результат:
      print("""<h1>Результат:</h1>""")
      print("""<p>Выполнено %d из %d задач</p>""" % (user["num_success_op"], user["num_op"]))
      print("""<h2>Успешно создан пользователь:</h2>""")
      print("""<h2>Имя:</h2>
      <p>%s</p>""" % user["fio"])
      print("""<h2>Логин:</h2>
      <p>%s</p>""" % user["login"])
      print("""<h2>Пароль:</h2>
      <p><span class="password">%s</span></p>""" % user["passwd"])
      print("""<h2>Префикс почты:</h2>
      <p>%s</p>""" % user["email_prefix"])
      print("""<h2>Почтовый ящик1:</h2>
      <p>%s</p>""" % user["email_server1"])
      print("""<h2>Почтовый ящик2:</h2>
      <p>%s</p>""" % user["email_server2"])
      print("<h2>Будьте внимательны с символами в пароле:</h2>")
      print("<p><span class='info'>1 - один, l - английская прописная Л, 0 - ноль, O - английская буква, I - английская большая И</span></p>")
      print("</body></html>")
      return True
  except Exception as e:
    log.error(get_exception_traceback_descr(e))
    return False

if __name__ == '__main__':
  log=logging.getLogger("add_new_domain_user")
  if conf.debug:
    log.setLevel(logging.DEBUG)
  else:
    log.setLevel(logging.INFO)

  # create the logging file handler
  fh = logging.handlers.TimedRotatingFileHandler(conf.log_path, when=conf.log_backup_when, backupCount=conf.log_backup_count)
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(funcName)s() %(levelname)s - %(message)s')
  fh.setFormatter(formatter)

  if conf.console:
    # логирование в консоль:
    stdout = logging.StreamHandler(sys.stdout)
    stdout.setFormatter(formatter)
    log.addHandler(stdout)

  # add handler to logger object
  log.addHandler(fh)

  log.info("Program started")
  if main()==False:
    log.error("error main()")
    sys.exit(1)
  log.info("Program success exit")
