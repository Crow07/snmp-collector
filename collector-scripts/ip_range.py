import yaml
import time
#import Queue
#import netsnmp
#import threading

start_time = time.time()
f = open('cfg.yaml')
info = yaml.load(f)

region = info['region']
device = info['device_model']
config = info['config']
print config[0]['test']['test1']
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
for n in range(len(config)):
    ip = info['config'][n]['ip']
    ip_range = get_ip(ip)
    print ip_range
