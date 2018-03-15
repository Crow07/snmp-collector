import netsnmp
import Queue
import time

start_time = time.time()
session = netsnmp.Session(Version=2, DestHost="172.31.6.112", Community="public",Timeout=3000000,Retries=0)
ret = session.get("1.3.6.1.4.1.2021")
rq = Queue.Queue()
rq.put(("172.31.6.112", "1.3.6.1.4.1.2021", ret, (time.time() - start_time)))
info = rq.get(block=False)
print ret
