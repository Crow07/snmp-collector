import yaml
import ast
f = open('cfg.yaml')
info = yaml.load(f)
config = info['config']
'''
for n in range(len(config)):
	ip = info['config'][n]['ip']
	metric = info['config'][n]['metric']
	for i in metric:
		print i
	n += 1
	print metric	

for n in range(len(config)):
	ip = info['config'][n]['ip']
    	vendor = info['config'][n]['vendor']
    	model = info['config'][n]['model']
    	metric_collection = info['config'][n]['metric']
    	for i in range(len(metric_collection)):
		print type(ip)
		metric = metric_collection[i]['key']
    		oid = metric_collection[i]['value']
	    	print ip,oid,metric  
'''
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

for n in range(len(config)):
    ip = info['config'][n]['ip']
    iplist = get_ip(ip)
    print iplist
    vendor = info['config'][n]['vendor']
    model = info['config'][n]['model']
    metric_collection = info['config'][n]['metric']
    for i in range(len(metric_collection)):
        metric = metric_collection[i]['key']
        oid = metric_collection[i]['value']
f.close()
