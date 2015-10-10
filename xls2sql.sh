#!/bin/bash
xls2csv -c'|' "${1}"|while read line
do
	fio="`echo $line|awk '{print $1}' FS='|'|sed 's/^ *//;s/^"*//;s/ *$//;s/"*$//'|sed 's/^ *//;s/ *$//'`"
	old_login="`echo $line|awk '{print $2}' FS='|'|sed 's/^ *//;s/^"*//;s/ *$//;s/"*$//'|sed 's/^ *//;s/ *$//'`"
	login="`echo $line|awk '{print $3}' FS='|'|sed 's/^ *//;s/^"*//;s/ *$//;s/"*$//'|sed 's/^ *//;s/ *$//'`"
	passwd="`echo $line|awk '{print $4}' FS='|'|sed 's/^ *//;s/^"*//;s/ *$//;s/"*$//'|sed 's/^ *//;s/ *$//'`"
	drsk_email="`echo $line|awk '{print $5}' FS='|'|sed 's/^ *//;s/^"*//;s/ *$//;s/"*$//'|sed 's/^ *//;s/ *$//'`"
	drsk_email_passwd="`echo $line|awk '{print $6}' FS='|'|sed 's/^ *//;s/^"*//;s/ *$//;s/"*$//'|sed 's/^ *//;s/ *$//'`"
	rsprim_email="`echo $line|awk '{print $7}' FS='|'|sed 's/^ *//;s/^"*//;s/ *$//;s/"*$//'|sed 's/^ *//;s/ *$//'`"
	hostname="`echo $line|awk '{print $8}' FS='|'|sed 's/^ *//;s/^"*//;s/ *$//;s/"*$//'|sed 's/^ *//;s/ *$//'`"
	ip="`echo $line|awk '{print $9}' FS='|'|sed 's/^ *//;s/^"*//;s/ *$//;s/"*$//'|sed 's/^ *//;s/ *$//'`"
	os="`echo $line|awk '{print $10}' FS='|'|sed 's/^ *//;s/^"*//;s/ *$//;s/"*$//'|sed 's/^ *//;s/ *$//'`"
	os_version="`echo $line|awk '{print $11}' FS='|'|sed 's/^ *//;s/^"*//;s/ *$//;s/"*$//'|sed 's/^ *//;s/ *$//'`"
	patches="`echo $line|awk '{print $12}' FS='|'|sed 's/^ *//;s/^"*//;s/ *$//;s/"*$//'|sed 's/^ *//;s/ *$//'`"

	doljnost="`echo $line|awk '{print $14}' FS='|'|sed 's/^ *//;s/^"*//;s/ *$//;s/"*$//'|sed 's/^ *//;s/ *$//'`"

	familiya="`echo $fio|awk '{print $1}' FS=' '|sed 's/^ *//;s/^"*//;s/ *$//;s/"*$//'|sed 's/^ *//;s/ *$//'`"
	name="`echo $fio|awk '{print $2}' FS=' '|sed 's/^ *//;s/^"*//;s/ *$//;s/"*$//'|sed 's/^ *//;s/ *$//'`"
	otchestvo="`echo $fio|awk '{print $3}' FS=' '|sed 's/^ *//;s/^"*//;s/ *$//;s/"*$//'|sed 's/^ *//;s/ *$//'`"

	add_user_name="импорт из xls"

	echo "insert into ad_users (fio,name,familiya,otchestvo,login,old_login,passwd,drsk_email,drsk_email_passwd,rsprim_email,rsprim_email_passwd,hostname,ip,os,os_version,patches,doljnost,add_time,add_ip,add_user_name) 	VALUES (\$\$${fio}\$\$,\$\$${name}\$\$,\$\$${familiya}\$\$,\$\$${otchestvo}\$\$,\$\$${login}\$\$,\$\$${old_login}\$\$,\$\$${passwd}\$\$,\$\$${drsk_email}\$\$,\$\$${drsk_email_passwd}\$\$,\$\$${rsprim_email}\$\$,\$\$-\$\$,\$\$${hostname}\$\$,\$\$${ip}\$\$,\$\$${os}\$\$,\$\$${os_version}\$\$,\$\$${patches}\$\$,\$\$${doljnost}\$\$,now(),\$\$${add_ip}\$\$,\$\$${add_user_name}\$\$);"
done
