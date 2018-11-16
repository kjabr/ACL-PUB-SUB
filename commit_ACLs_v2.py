#!/usr/bin/python
import subprocess
import sys
from kafka import KafkaProducer
from kafka.errors import KafkaError
import time

def make_new_file(new_file, target_content):
    # here we are writing a new file
    # this is the file that gets pulled
    outfile = open(new_file, 'w')
    outfile.write("\n".join(target_content))
    return

def convert_file(target_file):
    with open (target_file) as f:
        content = f.read().splitlines()
    f.close()

    # remove comments
    newcontent = [item for item in content if '#' not in item]

    # remove any empty lines
    newcontent1 = [item for item in newcontent if item != '']
    return newcontent1

def send_kafka(msg):
    producer = KafkaProducer(bootstrap_servers=['192.168.7.27:9092'])
    producer.send("ACL", b'%s' % msg)
# producer.send("test", b'')
    time.sleep(1)
    return

target_file = sys.argv[1]
newcontent = convert_file(target_file)

# New filename is whatever the filename + _commit
# Idea is to also allow someone to figure out the last change if needed

new_file_name = target_file + "_" + "commit"

# need to do some cleanup on the file, like remove comments and empty lines
make_new_file(new_file_name, newcontent)

# Now send a Kafka message with the write keyword "ACL_file_updated"
# and the actual file name
# remote nodes that receive the message would pull this file

send_kafka('ACL_file_updated %s' % new_file_name)

