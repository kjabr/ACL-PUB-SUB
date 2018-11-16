#!/usr/bin/python
import pycurl
import cStringIO
import binascii
import time
from kafka import KafkaConsumer
from kafka import TopicPartition
from cli import *

# The parser function acls_pretty. Receives the output of the ACLs and get back
# a list of lists that uses a dictionary where each list is indexed by its name

def acls_pretty (acl_lines):

# put ACLs in an array where each line is an item
    acl_lines1 = acl_lines.splitlines()
    acl_lines2 = [item.strip() for item in acl_lines1]

# find out how many ACLs we have
    acl_header_positions = [i for i, elem in enumerate(acl_lines2) if 'access list' in elem]
    acl_header_positions.append(len(acl_lines2))

# find the name of each ACL to be used as an index
    acl_headers = [item for item in acl_lines2 if 'access list' in item]
    acl_names = [item.split()[3] for item in acl_headers]

    acl_read = []
    acl_groups = []

# Seperate individual ACL lines (without headers) into lists
    for i in range(len(acl_header_positions)-1):
        acl_read = [item for item in
            acl_lines2[acl_header_positions[i]:acl_header_positions[i+1]]
                if ('permit' or 'deny') in item]
    # now group them into list of lists
        acl_groups.append(acl_read)

# now use ACL names as index keys for acl content lists
    acls_lists_of_lists = dict(zip(acl_names,acl_groups))
    return acls_lists_of_lists

# Now start listening to messages from the Kafka Server

kafka_server = "192.168.7.27:9092"
kafka_topic = "ACL"
fetched_acls = []

# Setup Kafka consumer in a loop
consumer = KafkaConsumer(bootstrap_servers=kafka_server)
consumer.assign([TopicPartition(kafka_topic, 0)])
print "Started listening to the " + kafka_topic + " Kafka topic"

for message in consumer:
    print ("Received Message from Kafka Server \n")
    if message.value == "exit":
        # not that useful here... just used for testing
        break
    if "ACL_file_updated" in message.value:
        # Looking for the right message that an ACL got updated
        # Fetch the ACL file from the server

        # looking for filename on the server in the Kafka message
        message_in_parts = (message.value).split()

        buf = cStringIO.StringIO()
        fetch_page = pycurl.Curl()
        fetch_page.setopt(fetch_page.URL, 'http://192.168.7.29/%s' % message_in_parts[1])
        fetch_page.setopt(fetch_page.WRITEFUNCTION, buf.write)
        fetch_page.perform()
        fetched_acls = buf.getvalue()

        # Get the local configured ACLs
        acl_show_output = cli("show access-list")

        # Reformat the output into a dictionary list where the ACL name is
        # the index
        local_acl_nested = acls_pretty(acl_show_output)

        # Convert ACLs we fetched into a dictionary list where the index is
        # the ACL name
        fetched_acls_nested = acls_pretty(fetched_acls)
        buf.close()

        # find common acl names between what is fetched to what is local..
        # That also means an ACL must get created locally on the device even
        # if it is empty
        #
        # Important: don't change ACLs that are in NOT the fetched list

        ACL_to_apply = []
        ACL_to_create = []

        fetched_keys = set(fetched_acls_nested.keys())

        # Find ACLs that got fetched but don't exit locally
        acls_not_local = [item for item in fetched_acls_nested.keys() if item
            not in local_acl_nested.keys()]

        # Create the ACLs that don't exist locally. Just empty for this step
        if len(acls_not_local) > 0:
            for new_key in acls_not_local:
                ACL_to_create.append("ip access-list " + new_key)
            CLI_CMDS = 'config t ; ' + ' ; '.join(ACL_to_create) + ' ; end'
            print "ACLs created:"
            print CLI_CMDS
            cli(CLI_CMDS)

        # Look for the difference between the ACEs that we fetched from the
        # server and the local (common) ACLs.
        # Create the ACEs if they don't exist
        for shared_key in fetched_keys:
            first_list = local_acl_nested[shared_key]
            second_list = fetched_acls_nested[shared_key]
            diff_list = [item for item in second_list if item not in first_list]
            # print ("diff: acl name %s ACLs: %s" % (shared_key, diff_list))
            ACL_to_apply.append("ip access-list " + shared_key)
            ACL_to_apply.extend(diff_list)

            CLI_CMDS = 'config t ; ' + ' ; '.join(ACL_to_apply) + ' ; end'

        # Apply (and print) changes to local config
        print 'Changes to local config:'
        print '\n'.join(ACL_to_apply)
        cli(CLI_CMDS)

        
