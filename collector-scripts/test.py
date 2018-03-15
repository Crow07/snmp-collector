import yaml
import time
import Queue
import netsnmp
import threading

start_time = time.time()
f = open('cfg.yaml')
info = yaml.load(f)
region = info['region']
print region

f.close()
