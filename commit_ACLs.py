#!/usr/bin/python
import subprocess
import sys
from kafka import KafkaProducer
from kafka.errors import KafkaError
import time

def send_kafka(msg):
    producer = KafkaProducer(bootstrap_servers=['192.168.7.27:9092'])
    producer.send("ACL", b'%s' % msg)
# producer.send("test", b'')
    time.sleep(1)
    return

send_kafka('ACL_file_updated %s' % sys.argv[1])

# subprocess.call("cp", sys.argv[1], sys.argv[1]+str(time.time()))
