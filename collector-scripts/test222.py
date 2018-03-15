import yaml
import time
import Queue
import netsnmp
import threading
import json

start_time = time.time()
f = open('cfg.yaml')
info = yaml.load(f)

region = info['region']
device = info['device_model']
config = info['config']

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
    start,end = [ip2num(x) for x in ip.split('-') ]
    return [ num2ip(num) for num in range(start,end+1) if num & 0xff ]

##snmp 
class SnmpClass(object):

    def __init__(self, oid, version, destHost, community):
        self.oid = oid
        self.version = version
        self.destHost = destHost
        self.community = community
    @property
    def query(self):
        """
        snmpget
        """
        try:
            result = netsnmp.snmpget(self.oid,
                                      Version=self.version,
                                      DestHost=self.destHost,
                                      Community=self.community)
        except Exception, err:
            print err
            result = None
        return result
 	print result
 
data = []

for n in range(len(config)):
    ip = info['config'][n]['ip']
    iplist = get_ip(ip)
    vendor = info['config'][n]['vendor']
    model = info['config'][n]['model']
    metric_collection = info['config'][n]['metric']
    for addr in iplist:
   	host = addr
	for i in range(len(metric_collection)):
	        metric = metric_collection[i]['key']
	        oid = metric_collection[i]['value']
    		ret = SnmpClass(oid= "sysName", destHost= host, version= 2, community= "public").query
    		record = {}
		record['metric'] = metric
		record['endpoint'] = host
		record['timestamp'] = int(time.time())
		record['step'] = 60
		record['value'] = ret
		record['counterType'] = 'GAUGE'
		record['tags'] = 'vendor=%s' % vendor
		data.append(record)
f.close()
if data:
    print json.dumps(data)



