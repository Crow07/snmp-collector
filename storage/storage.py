#! /usr/bin/env python
#-*- coding:utf-8 -*-

import yaml
import time
import Queue
import netsnmp
import threading
import json
import xlrd
import os
import codecs
import urllib2

start_time = time.time()
metric_file = open('../config/storage_cfg.yaml')
metric = yaml.load(metric_file)
metric_collection = metric['StorageMetric']

info_file = "/var/log/collector/check_storage_info.log"
f =open(info_file)
json_data =json.loads(f.read())

myq = Queue.Queue()
rq = Queue.Queue()

def snmpMethod(method,session,metric,var_list,oid,host):
    if method == 'GET':
        ret = str(session.get(var_list))[2:-3]
        rq.put((host, metric, oid, ret, (time.time() - start_time)))
    elif method == 'WALK':
        collections = netsnmp.VarList(netsnmp.Varbind(oid))
        collection_vals = session.walk(collections)
	num =1
        for col in collections:
            tag = col.tag
            iid = col.iid
            val = col.val
            if tag == "hrProcessorLoad" and num ==1:
                ret = len(collections)
                metric = "Processers"
		num +=1
		rq.put((host, metric, oid, ret, (time.time() - start_time)))
            elif tag == "ifAdminStatus" or tag == "ifInOctets" or tag == "ifOutOctets" or tag == "ifHighSpeed":
                interface_var = netsnmp.VarList(netsnmp.Varbind('.1.3.6.1.2.1.2.2.1.2'))
                interface_list = session.walk(interface_var)
                interfaces = {}
                for interface in interface_var:
                    interface_dict1 = {interface.iid : interface.val}
                    interfaces = dict(interfaces, **interface_dict1)
                if interfaces.has_key(iid):
                    metric = tag + '.' + interfaces[iid]
                    ret = val
                    rq.put((host, metric, oid, ret, (time.time() - start_time)))
            elif tag == "hrDiskStorageCapacity":
                disk_var = netsnmp.VarList(netsnmp.Varbind('HOST-RESOURCES-MIB::hrDeviceDescr'))
                disk_list = session.walk(disk_var)
                disks = {}
                for disk in disk_var:
                    if 'SCSI' in disk.val:
                        disk_dic = {disk.iid : disk.val}
                        disks = dict(disks,**disk_dic)
                if disks.has_key(iid):
                    metric = tag + '.' + disks.get(iid)
                    ret = val
                    rq.put((host, metric, oid, ret, (time.time() - start_time)))
            elif tag == "hrStorageAllocationUnits" or tag == "hrStorageSize" or tag == "hrStorageUsed":
                storage_var = netsnmp.VarList(netsnmp.Varbind('HOST-RESOURCES-MIB::hrStorageDescr'))
                storage_list = session.walk(storage_var)
                storages = {}
                for storage in storage_var:
                    if '/' in storage.val:
                        storage_dic = {storage.iid: storage.val}
                        storages = dict(storages,**storage_dic)
                if storages.has_key(iid):
                    metric = tag + '.' + storages.get(iid)
                    ret = val
                    rq.put((host, metric, oid, ret, (time.time() - start_time)))
            elif tag == "diskIOLA5" or tag == "diskIONRead" or tag == "diskIONWritten" or tag == "diskIOReads" or tag == "diskIOWrites":
                diskio_var = netsnmp.VarList(netsnmp.Varbind('UCD-DISKIO-MIB::diskIODevice'))
                diskio_list = session.walk(diskio_var)
                diskios = {}
                for diskio in diskio_var:
                    if 'sd' in diskio.val or 'vd' in diskio.val or 'hd' in diskio.val:
                        diskio_dic = {diskio.iid:diskio.val}
                        diskios = dict(diskios, **diskio_dic)
                if diskios.has_key(iid):
                    metric = tag + '.' + diskios.get(iid)
                    ret = val
                    rq.put((host, metric, oid, ret, (time.time() - start_time)))

            else:
                #print tag,iid,val,oid,host
		continue
    else:
        print "method Error"

data = []
s = set()
def b():
    for i in json_data:
	if i['metric'] == 'snmp_status':
	    if i['value'] == 1:
                if i['endpoint'] not in s:      
		    host = i['endpoint']
		    s.add(host)
		    community = i['tags']['community']
		    snmpVersion = i['tags']['snmpVersion']
		    region = i['tags']['region']
		    community = i['tags']['community']
		    SecLevel = i['tags']['SecLevel']
		    SecName = i['tags']['SecName']
		    PrivPass = i['tags']['PrivPass']
		    AuthPass = i['tags']['AuthPass']
		    model = i['tags']['model']
		    for kv in metric_collection:
			if model == kv['model']:
			    for n in  kv['metric']:
				method = n['method']
				oid = n['oid']
				metric = n['key']
				var_list = netsnmp.VarList()
				var_list.append(netsnmp.Varbind(oid))
				if snmpVersion == 2:
				    session =  netsnmp.Session(Version=2, DestHost=host, Community=community,Timeout=3000,Retries=0)
				else:
				    session =  netsnmp.Session(Version=3,DestHost=host,SecLevel=SecLevel,SecName=SecName,PrivPass=PrivPass,AuthPass=AuthPass)
				snmpMethod(method,session,metric,var_list,oid,host)
		    while True:
			try:
			    info = rq.get(block=False)
			    record = {}
			    record['metric'] = info[1]
			    record['endpoint'] = info[0]
			    record['timestamp'] = int(time.time())
			    record['step'] = 60
			    record['value'] = info[3]
			    record['counterType'] = 'GAUGE'
			    record['tags'] = 'region=%s' % region
			    data.append(record)
		        except Queue.Empty:
		            break
thread_num = 100
threads=[]
for i in range(thread_num):
    th=threading.Thread(target=b,args=())
    th.start()
    threads.append(th)
for t in threads:
    t.join()
metric_file.close()
if data:
    print json.dumps(data)
