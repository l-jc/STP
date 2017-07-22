#Lsr.py

import sys
import socket
from time import *
from threading import *
from thrd import *
from node import *
from func import *

total = len(sys.argv)
if total != 4: # wrong input
	print "usage: python Lsr.py NODE_ID NODE_PORT CONFIG.TXT\n"
	exit(-1)
else: # read the parameters
	node_id = str(sys.argv[1])
	node_port = int(sys.argv[2])
	config_file_name = str(sys.argv[3])
	
# create a UDP socket
node_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
node_socket.bind(('',node_port))

	
# read the config file
config_file = open(config_file_name,'r')
num_of_neighbours = int(config_file.readline())
tmp_neighbour_list = {}
for i in range(num_of_neighbours):
	next_line = config_file.readline()
	next_line = next_line.split()
	neighbour_node = next_line[0]
	link_weight = float(next_line[1])
	neighbour_port = int(next_line[2])
	tmp_neighbour_list[neighbour_node] = (link_weight, neighbour_port)
config_file.close()
# print tmp_neighbour_list

# create a Node instance
bcast = []
node = Node(node_id,node_port,tmp_neighbour_list,node_socket)


# start to send distance vector messages and heartbeat messages
print "initiating node%s..." % node_id,
node.initiateNode()
print "\tdone!"


# infinite loop
while True:
	try:
		# wait for receiving a message.
		msg, addr = node_socket.recvfrom(1024)
		segments = msg.split('\n')
		# print segments
		# print "received %s" % str(segments)
		if segments[0] == '0': # msg is a DV
			# print "received dv"
			msgtype = segments[0]
			sender = segments[1]
			timestamp = segments[2]
			info = segments[3]
			# node.resets[sender].set() # reset the timer for sender
			if not (sender,timestamp) in bcast: # msg has not been broadcast yet
				# broadcast it
				node.floodout(msg)
				# create new dv
				newdv = string2dict(sender,info)
				#print "update", newdv
				# update topology
				node.update(newdv)
				# update node.bcast
				bcast.append((segments[1],segments[2]))
				if len(bcast) >= 100:
					del bcast[0]
				# print len(bcast)
		elif segments[0] == '1': # is a HB msg
			sender = segments[1]
			# print "recieve hb from %s" % sender
			node.resets[sender].set()

	except KeyboardInterrupt:
		node.terminateNode()
		print "\nDetected KeyboardInterrup.\nNode stopped working."
		break
	

node.terminateNode()
node_socket.close()
