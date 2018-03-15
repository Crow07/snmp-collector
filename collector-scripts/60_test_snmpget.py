import yaml
import time
import Queue
import netsnmp
import threading
import json
start_time = time.time()
f = open('cfg.yaml')
cfg = yaml.load(f)

region = cfg['region']
device = cfg['device_model']
config = cfg['config']

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

myq = Queue.Queue()
rq = Queue.Queue()
data = []

for n in range(len(config)):
    ip = config[n]['ip']
    iplist = get_ip(ip)
    vendor = config[n]['vendor']
    model = config[n]['model']
    metric_collection = config[n]['metric']
    for host in iplist:
        for kv in metric_collection:
        	oid = kv['oid']
        	metric = kv['key']
        	myq.put((host, oid, metric))
    def poll_one_host():
    	while True:
            try:
                host, oid, metric = myq.get(block=False)
                session = netsnmp.Session(Version=2, DestHost=host, Community="public",Timeout=3000,Retries=0)
                var_list = netsnmp.VarList()
                var_list.append(netsnmp.Varbind(oid))
                ret = str(session.get(var_list))[2:-3]
                rq.put((host, metric, oid, ret, (time.time() - start_time)))
            except Queue.Empty:
                break
    thread_arr = []
 
    num_thread = 1
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
                    

