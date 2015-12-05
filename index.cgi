#!/usr/bin/env python
# -*- coding: utf-8 -*-
import config as conf

print("""
<html>
<HEAD>
<META HTTP-EQUIV="CONTENT-TYPE" CONTENT="text/html; charset=utf-8">
<TITLE>Добавление пользователя в домен</TITLE>
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
.normaltext {
}
</style>
<style>
.ele_null {
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

<body><h1>Добавление нового пользователя в домен</h1>

<form method=POST action="add_new_domain_user.cgi">
<P><B>Фамилия:</B>
<P><input type=text name=user_familia>

<P><B>Имя:</B>
<P><input type=text name=user_name>

<P><B>Отчество:</B>
<P><input type=text name=user_otchestvo>

<P><B>Описание (отдел, район. Например: '(ШРЭС) инженер 2-й категории'):</B>
<P><input type=text name=user_description>

<div align="left">
<P><B>Район: </B><br>
""")
checked="checked"
for uid in conf.default_groups:
	print("""
<input type="radio" name="ou_name" value="%(id)s" %(checked)s> %(name)s<br>
""" % {\
	"id":uid,\
	"name":conf.default_groups[uid]["name"].encode("utf8"),\
	"checked":checked
	})
	checked=""
#<input type="radio" name="ou_name" value="filial2">Южные сети<br>
print("""
</div>

<P><input type=submit>
</form>

<p>Посмотреть список пользователей можно по 
<a target="_self" 
href="show_user_ad_list.cgi"
>
ссылке
</a>.
</p>


</body></html>
""")
