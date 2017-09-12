# ACL-PUB-SUB
Use ACLs in a Pub-Sub model on Cisco switches and Routers

## Problem Statement:

Imagine ACLs that live on many switches and routers. Currently to keep them up to date requires an admin or a tool to connect to each device to make the change. Doesn't matter if that is done via SSH or an API. If you have hundreds or even thousands of devices that becomes pretty cumbersome. This project solves this problem.

## Solution:
 
- Centralize the ACLs on a server. Say a Linux server. Where it allows the admin to make the add/remove ACLs. 
- Use a notification channel (Kafka in this project) where the network devices would get a quick alert that an update is available.
- On the network devices pull the appropriate ACL file from the centralized server. Here using an http-GET using PyCurl
- Network devices receive the updated list. Check the ACLs running locally. Calculate the diff and then apply the changes
- Network devices wait for the next notification and then next update

## Components:

The solution needs 3 parts to make it work:
- Cisco switches and routers with Guestshell (the code here was tested with Nexus 9ks but with some minor work can be made to work on all Cisco switches and routers that have implemented the Guestshell)
- A server to run the Kafka server (broker)
- A web server to serve the ACL file

## Demo

### On the Kafka Server:

Launch ZooKeeper and Kafka server on the Kafka server with a topic called "ACL". Ensure the Kafka server listens on the local IP address.

### On the Web server:

If not already running, install a web server daemon (say Apache2) on the web server. Then install the Kafka Python module:

`pip install kafka-python`

Then copy the file "commit-ACLs.py" to the web server. Create a file called "CA_Security_ACL_list_2017" in the /var/www/html directory. This would contain your ACLs. The format of the ACLs is simple. Here's an example:

```
root@Linux1:/var/www/html# more CA_Security_ACL_list_2017 
ip access list test
10 permit ip any 10.0.0.0/8
40 permit ip any 172.16.0.0/16
50 permit ip any 192.168.0.0/16
ip access list test3
20 permit ip any 20.0.0.0/8
30 permit ip any 22.22.22.22/32
ip access list test4
10 permit ip any 1.1.1.1/32
20 permit ip 192.168.7.4/32 143.10.5.1/32
30 permit ip 192.168.7.5/32 143.18.5.1/32
40 permit ip 192.168.7.6/32 143.18.5.1/32
no 50 permit ip 192.168.8.7/32 2.2.2.2/32
```
You may want to place the commit_ACLs.py file in the same directory to make it a little easier to run.

### On the Cisco switch (running NX-OS for example):

Guestshell, at least with NX-OS, uses the mgmt port to communicate out. So you want to first make sure the mgmt0 interface on the Nexus switch can reach the Kafka server and also the web server. Ping both to make sure it is working. In some cases you may need to add a route to the VRF context:

```
vrf context management
  ip route 0.0.0.0/0 172.16.1.2
```

Now get into Guestshell using (guestshell command) and install the Kafka Python module. You can do it like this:

- Change the VRF on guestshell to management:

`chvrf management`

- Add DNS to the /etc/resolv.conf file. For example:

```
[guestshell@guestshell ~]$ more /etc/resolv.conf 
nameserver 208.67.222.222
nameserver 208.67.220.220
```

- Now install the Kafka Python module:

`pip install kafka-python`

- Create a file called (for example) "pub-sub-acls.py" and copy and paste the contents of pub-sub-acls.py file in this project or transfer the file somehow to Guestshell. For a demo the copy/paste seems easy but for a large environment you probably want to automate this part.

### Run the demo

- Create an ACL on the switch, called, for example, 'test'
- On the webserver add the ACL to the "CA_Security_ACL_list_2017" file with whatever ACEs you want
- In Guestshell on the switch launch your Python script in the background:

`./acl_sub.py &`

If you get errors that the script can't reach the Kafka server it probably means you didn't do a 'chvrf management'. And make sure that Guestshell can ping both servers.

- On the webserver send out a notification that the file is updated:

`./commit_ACLs.py CA_Security_ACL_list_2017`

Note commit_ACLs.py script takes one argument. The filename in this case. In a more realistic environment you may want to add the Kafka topic name. That way you would associate the ACL file to a topic name. Network devices subscribe to a specific topic and hence the Kafka topic is how you would segment the places in the network.

Now go back to the Nexus CLI (type exit a couple of times). Check the ACL content. It should get updated by whatever on the webserver. Make changes to the file on the webserver, run the commit_ACLs.py script, and a moment later it would get updated on the local device.

You can have few or many switches (as in this example) gettting updated at about the same time. That is the goal of this project.

## Notes:

- The solution scales pretty well. You can easily scale up the web server using a server with big CPU/memory, or use multiple servers to load balance. Kafka server can be scaled up into a cluser

- The Kafka Topic is a key to leverage across multiple parts of the network. For example a topic can be setup for campus switches, and another for data center switches, and perhaps another for branch routers.

- The notification sent via Kafka includes the file name already. However the script included at the moment only retrieves the "CA_Security_ACL_list_2017" file. A little more can be made to make that match what is in the notification. Here you would have a different ACL list for different Kafka topics.

