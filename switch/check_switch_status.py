#! /usr/bin/env python
# -*- coding:utf-8 -*-
import json
import xlrd
import urllib2
import time
import os
import codecs
import netsnmp
import threading
import Queue

start_time = time.time()
file_path = '../config/static_config.xlsx'

def Excel2Json(file_path):
    if get_data(file_path) is not None:
        book = get_data(file_path)
        sheet = book.sheet_by_name("network")
        row_0 = sheet.row(0)  
        nrows = sheet.nrows  
        ncols = sheet.ncols
        result = []
        for i in range(nrows):
            if i == 0:
                continue
            tmp = {}
            for j in range(ncols):
                title_de = str(row_0[j])
                title_cn = title_de.split("'")[1].strip()
                tmp[title_cn] = sheet.row_values(i)[j]
            result.append(tmp)
        return result


def get_data(file_path):
    try:
        data = xlrd.open_workbook(file_path)
        return data
    except Exception, e:
        print u'excel表格读取失败：%s' % e
        return None

##ip rules
def ip2num(ip):
    ip=[int(x) for x in ip.split('.')]
    return ip[0] <<24 | ip[1]<<16 | ip[2]<<8 |ip[3]

def num2ip(num):
    return '%s.%s.%s.%s' %( (num & 0xff000000) >>24,
                            (num & 0x00ff0000) >>16,
                            (num & 0x0000ff00) >>8,
                            num & 0x000000ff )
def get_ip(ip):
    if "," in ip:
        ip_range = ip.split(',')
        iplist = []
        for i in ip_range:
            if '-' in i:
                start,end = [ip2num(x) for x in i.split('-') ]
                ipl =  [ num2ip(num) for num in range(start,end+1) if num & 0xff ]
                iplist += ipl
            else:
                ipl = [i]
                iplist += ipl
        return iplist
    elif '-' in ip and ',' not in ip:
        start,end = [ip2num(x) for x in ip.split('-') ]
        ipl =  [ num2ip(num) for num in range(start,end+1) if num & 0xff ]
        return ipl
    else:
        return [ip]

#check status
check_log = '/var/log/collector/check_switch.err'
f_err = open(check_log, 'w')
def check_connect(ip):
    host_status = os.popen('ping -c 1 -w 1 %s|grep "0 received"' % (ip)).read()
    if '0 received' in host_status:
        return 0
    else:
        return 1
def check_status(ip,community,snmpVersion,SecLevel,SecName,PrivPass,AuthPass):
    ping = check_connect(ip)
    testsnmp = netsnmp.Varbind('sysName')
    varlist = netsnmp.VarList(testsnmp)
    if snmpVersion == 2:
        session =  netsnmp.Session(Version=2, DestHost=ip, Community=community,Timeout=2000,Retries=0)
    elif snmpVersion == 3:
	if SecLevel == 'authPriv':
    	    session =  netsnmp.Session(Version=3, DestHost=ip,SecLevel=SecLevel,SecName=SecName,PrivPass=PrivPass,AuthPass=AuthPass)
        else:
	    status =  {'connect_status': 0, 'snmp_status': 0}
	    return status
    if ping == 0:
        status = {'connect_status': ping, 'snmp_status': 0}
	f_err.write('ping error ' + ip + '\n')
        return status
    else:
	snmp_status = session.get(varlist)
	if not snmp_status:
            snmp = 0
	    f_err.write('snmp error ' + ip + '\n')
        else:
            snmp = 1
        status = {'connect_status': ping, 'snmp_status': snmp}
        return status
#handle iprange to list
json_data = Excel2Json(file_path)
data = []
for i in json_data:
    iplist = get_ip(i['ip_range'])
    snmpVersion = i['snmp_version']
    region = i['region']
    model = i['model']
    community = i['community']
    SecLevel = i['SecLevel']
    SecName = i['SecName']
    PrivPass = i['PrivPass']
    AuthPass = i['AuthPass']
    for ip in iplist:
	info = {}
	info['snmpVersion']  = snmpVersion
	info['model'] = model
	info['region'] = region
	info['community'] = community
	info['SecLevel'] = SecLevel
	info['SecName'] = SecName
	info['PrivPass'] = PrivPass
	info['AuthPass'] = AuthPass
	info['ip'] = ip
	data.append(info)
#check
s = set()
data_json = []
print_json = []
def a():
    for i in data:
	if i['ip'] not in s:
	    s.add(i['ip'])
	    ip = i['ip']
	    community = i['community']
	    snmpVersion = i['snmpVersion']
	    SecLevel = i['SecLevel']
  	    SecName = i['SecName']
   	    PrivPass = i['PrivPass']
  	    AuthPass = i['AuthPass']
	    model = i['model']
	    tags = {}
            tags['SecLevel'] = SecLevel
            tags['region'] = region
            tags['SecName'] = SecName
            tags['PrivPass'] = PrivPass
            tags['AuthPass'] = AuthPass
	    tags['community'] = community
	    tags['snmpVersion'] = snmpVersion
	    tags['model'] = model
	    status = check_status(ip,community,snmpVersion,SecLevel,SecName,PrivPass,AuthPass)
            connect_status = status['connect_status']
 	    snmp_status = status['snmp_status']
	    record_conn = {}
	    record_conn['metric'] = 'connect_status'
            record_conn['endpoint'] = ip
            record_conn['value'] = connect_status
            record_conn['tags'] = tags
            data_json.append(record_conn)
	    record_snmp = {}
            record_snmp['metric'] = 'snmp_status'
            record_snmp['endpoint'] = ip
            record_snmp['value'] = snmp_status
            record_snmp['tags'] = tags
	    data_json.append(record_snmp)
	    print_conn = {}
	    print_conn['metric'] = 'connect_status'
            print_conn['endpoint'] = ip
            print_conn['timestamp'] = int(time.time())
            print_conn['step'] = 60
            print_conn['value'] = connect_status
            print_conn['counterType'] = 'GAUGE'
            print_json.append(print_conn)
            print_snmp = {}
            print_snmp['metric'] = 'snmp_status'
            print_snmp['endpoint'] = ip
            print_snmp['timestamp'] = int(time.time())
            print_snmp['step'] = 60
            print_snmp['value'] = snmp_status
            print_snmp['counterType'] = 'GAUGE'
            print_json.append(print_snmp)
	    
thread_num = 100
threads=[]
for i in range(thread_num):
    th=threading.Thread(target=a,args=())
    th.start()
    threads.append(th)
for t in threads:
    t.join()
#if data_json:
print json.dumps(print_json)
file_path = '/var/log/collector/check_switch_info.log'
f = open(file_path, 'w')  
f.write(json.dumps(data_json))
f.close()
f_err.close()
