#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import ldap
import re
import config as conf
import traceback

log = None
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

def get_exception_traceback_descr(e):
  if hasattr(e, '__traceback__'):
    tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
    result=""
    for msg in tb_str:
      result+=msg
    return result
  else:
    return e

def init(log_in):
  global ldap_url
  global ldap_user
  global ldap_passwd
  global log
  try:
    if log is None:
      log = log_in
    # http:
    #ad = ldap.initialize(ldap_url)
    #ad.set_option(ldap.OPT_REFERRALS,0)
    #ad.simple_bind_s(ldap_user,ldap_passwd)

    # https:
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
    ad = ldap.initialize(conf.LDAP_SERVER)
    ad.simple_bind_s(conf.BIND_DN, conf.BIND_PASS)
  except ldap.LDAPError as desc:
    log.error(desc)
    return None
  except Exception as e:
    log.error(get_exception_traceback_descr(e))
    return None
  return ad


def get_computers(ad):
  global log
  comps={}
  try:
    #basedn = 'DC=drsk,DC=rao-esv,DC=ru'
    basedn = conf.base_comp_dn
    scope = ldap.SCOPE_SUBTREE
    filterexp = '(&(objectCategory=Computer)(objectClass=Computer)(cn=RSK40*))'
    attrlist = ['cn','description']
    page_size = 500 # how many users to search for in each page, this depends on the server maximum setting (default highest value is 1000)
    req_ctrl = ldap.controls.libldap.SimplePagedResultsControl(criticality=True, size=page_size, cookie='')
    msgid = ad.search_ext(basedn, scope, filterexp, attrlist,serverctrls=[req_ctrl])

    total_results = []
    pages = 0

    while True: # loop over all of the pages using the same cookie, otherwise the search will fail
      pages += 1
      rtype, rdata, rmsgid, serverctrls = ad.result3(msgid)
      for user in rdata:
        total_results.append(user)

      # меняем сложное формирование списка:
      #pctrls = [c for c in serverctrls if c.controlType == ldap.controls.libldap.SimplePagedResultsControl.controlType]
      # на простое формирование списка:
      pctrls = None
      for item in serverctrls:
        if item.controlType == ldap.controls.libldap.SimplePagedResultsControl.controlType:
          pctrls = [item]

      if pctrls:
        if pctrls[0].cookie: # Copy cookie from response control to request control
          req_ctrl.cookie = pctrls[0].cookie
          msgid = ad.search_ext(basedn, scope, filterexp, attrlist,serverctrls=[req_ctrl])
        else:
          break
      else:
        break
    log.debug("count of get computers=%d"%len(total_results))
    for result in total_results:
      comp={}
      comp["name"]=result[1]['cn'][0].decode('utf-8')
      comp["full_name"]="%s.drsk.ru" % result[1]['cn'][0].decode('utf-8').lower()
      if "description" in result[1]:
        comp["description"]=result[1]['description'][0].decode('utf-8')
      comps[comp["name"]]=comp
    return comps
  except ldap.LDAPError as desc:
    log.error(desc)
    return None
  except Exception as e:
    log.error(get_exception_traceback_descr(e))
    return None

def get_users(ad):
  global log
  users={}
  try:
    basedn = conf.base_user_dn
    scope = ldap.SCOPE_SUBTREE
    filterexp = '(sAMAccountName=*)'
    attrlist = ['sAMAccountName','descrption','givenName','sn','mail','userWorkstations','initials','displayName','info','displayNamePrintable','canonicalName','ms-DS-UserAccountAutoLocked','msDS-UserAccountDisabled','msDS-UserDontExpirePassword','msDS-UserPasswordExpired','UserAccountControl','msDS-PhoneticLastName']
    #attrlist = ['cn']
    page_size = 500 # how many users to search for in each page, this depends on the server maximum setting (default highest value is 1000)
    req_ctrl = ldap.controls.libldap.SimplePagedResultsControl(criticality=True, size=page_size, cookie='')
    msgid = ad.search_ext(basedn, scope, filterexp, attrlist,serverctrls=[req_ctrl])

    total_results = []
    pages = 0

    while True: # loop over all of the pages using the same cookie, otherwise the search will fail
      pages += 1
      rtype, rdata, rmsgid, serverctrls = ad.result3(msgid)
      for user in rdata:
        total_results.append(user)

      # меняем сложное формирование списка:
      #pctrls = [c for c in serverctrls if c.controlType == ldap.controls.libldap.SimplePagedResultsControl.controlType]
      # на простое формирование списка:
      pctrls = None
      for item in serverctrls:
        if item.controlType == ldap.controls.libldap.SimplePagedResultsControl.controlType:
          pctrls = [item]

      if pctrls:
        if pctrls[0].cookie: # Copy cookie from response control to request control
          req_ctrl.cookie = pctrls[0].cookie
          msgid = ad.search_ext(basedn, scope, filterexp, attrlist,serverctrls=[req_ctrl])
        else:
          break
      else:
        break
    log.debug("count of get users=%d"%len(total_results))
    for result in total_results:
      user={}
      user["account_name"]=result[1]['sAMAccountName'][0].decode('utf-8')
      user["attr"]=int(result[1]['userAccountControl'][0].decode('utf-8'))
      if "givenName" in result[1]:
        user["firstname"]=result[1]['givenName'][0].decode('utf-8')
      if "description" in result[1]:
        user["description"]=result[1]['description'][0].decode('utf-8')
      if "sn" in result[1]:
        user["secondname"]=result[1]['sn'][0].decode('utf-8')
      if "mail" in result[1]:
        user["mail"]=result[1]['mail'][0].decode('utf-8')
      if "msDS-PhoneticLastName" in result[1]:
        user["maiden_name"]=result[1]['msDS-PhoneticLastName'][0].decode('utf-8')
      if "canonicalName" in result[1]:
        user["full_name"]=re.sub(r'.*/','',result[1]['canonicalName'][0].decode('utf-8'))
  except ldap.LDAPError as desc:
    log.error(desc)
    return None
  except Exception as e:
    log.error(get_exception_traceback_descr(e))
    return None
  return users
