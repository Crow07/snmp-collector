#! /usr/bin/env python
#-*- coding:utf-8 -*-

import yaml
import time
import Queue
import netsnmp
import threading
import json

start_time = time.time()
f = open('/root/scripts/collector-scripts/snmpwalk/cfg.yaml') ##路径写全路径或者相对路径
cfg = yaml.load(f)

region = cfg['region']
device = cfg['device_model']
config = cfg['config']
myq = Queue.Queue()
rq = Queue.Queue()
data = []

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

def Snmpv2(host, community, oid, method, metric):
    session =  netsnmp.Session(Version=2, DestHost=host, Community=community,Timeout=3000,Retries=0)
    var_list = netsnmp.VarList()


    if method == 'GET':
        var_list.append(netsnmp.Varbind(oid))
        #ret = session.get(var_list)
	ret = str(session.get(var_list))[2:-3]
        rq.put((host, metric, oid, ret, (time.time() - start_time)))
    elif method == 'WALK':
        collections = netsnmp.VarList(netsnmp.Varbind(oid))
        collection_vals = session.walk(collections)
        for col in collections:
	    tag = col.tag
            iid = col.iid
            val = col.val
            if tag == "hrProcessorLoad":
                ret = len(collections)
                metric = "Processers"
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
                print tag,iid,val,oid,host
    else:
        print "method Error"

for n in range(len(config)):
    ip = config[n]['ip']
    iplist = get_ip(ip)
    vendor = config[n]['vendor']
    model = config[n]['model']
    metric_collection = config[n]['metric']
    snmpversion = config[n]['SnmpVersion']['version']
    community = config[n]['SnmpVersion']['community']
    for host in iplist:
        for kv in metric_collection:
            method = kv['method']
            oid = kv['oid']
            metric = kv['key']
            myq.put((host, oid, metric, method))
    def poll_one_host():
        while True:
            try:
                host, oid, metric,method = myq.get(block=False)
                Snmpv2(host, community, oid, method, metric)
            except Queue.Empty:
                break
    thread_arr = []
 
    num_thread = 50
    for i in range(num_thread):
        t = threading.Thread(target=poll_one_host, kwargs={})
        t.setDaemon(True)
        t.start()
        thread_arr.append(t)
     
    for i in range(num_thread):
        thread_arr[i].join()
     
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
            record['tags'] = 'vendor=%s' % vendor
            data.append(record)
        except Queue.Empty:
                print time.time() - start_time
                break
f.close()
if data:
    print json.dumps(data)

