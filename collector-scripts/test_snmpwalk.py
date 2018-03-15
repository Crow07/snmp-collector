#!/usr/bin/env python
#cofing:utf-8
import netsnmp

session = netsnmp.Session(Version=2, DestHost="172.31.6.112", Community="public",Timeout=3000,Retries=0)
vars = netsnmp.VarList(netsnmp.Varbind('UCD-DISKIO-MIB::diskIOLA5'))
vals = session.walk(vars)
test = {}
print vals
for var in vars:
    print var.tag, var.iid, var.val, var.type
    qqq = {var.iid:var.val}
    test = dict(test,**qqq)
print test
    

    
