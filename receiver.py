# 2
# receiver.py

import sys
import socket
import random
import time
from stp import *

test = False

total = len(sys.argv)
if total != 3:
	print "python receiver.py receiver_port file.txt"
	exit(-1)
else:
	receiver_port = int(sys.argv[1])
	file_name = str(sys.argv[2])

# set up udp socket
receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver_socket.bind(('', receiver_port))

next_seq = 100
next_ack = 0

# open log file
log = open("receiver_log.txt",'w')
if not log:
	print "Can't create log file."
	exit(-3)

# set up start time
start_time = time.time()

# handshake
next_seq, next_ack, mws, mss, sender_address = grantConnection(receiver_socket,next_seq,next_ack,start_time,log)

# expected in-order packet seqno
base_recv = next_ack
firstb = next_ack

# open the file
file = open(file_name,'w')
if not file:
	print "Can not create file."
	exit(-2)

windows = Window(mws/mss,0,start_time,log)
pkt_recv = 0 # number of data segments received
dup_data = 0 # number of duplicate data segments received

while True:
	recvmsg, ad = receiver_socket.recvfrom(mss + sys.getsizeof(WinBuffer))
	pkt_recv += 1
	recvpkt = processMsg(recvmsg)
	data = recvpkt.data
	#log.write("rcv\t\t%f\tD\t%d\t%d\t%d\n" % (float(time.time()-start_time), recvpkt.head.seqno, len(data), recvpkt.head.ackno))
	if recvpkt.head.fin: # receive FIN packet
		log.write("rcv\t\t%f\tF\t%d\t%d\t%d\n" % (float(time.time()-start_time), recvpkt.head.seqno, len(data), recvpkt.head.ackno))
		print "Connection Terminating..."
		pkt_recv -= 1
		lastb = next_ack
		# send back fin ack
		pkt = WinBuffer(Header(next_seq,next_ack,1,0,1))
		receiver_socket.sendto(str(pkt),sender_address)
		log.write("snd\t\t%f\tFA\t%d\t%d\t%d\n" % (float(time.time()-start_time), pkt.head.seqno, 0, pkt.head.ackno))
		# send fin
		pkt = WinBuffer(Header(next_seq,next_ack,0,0,1))
		receiver_socket.sendto(str(pkt),sender_address)
		log.write("snd\t\t%f\tF\t%d\t%d\t%d\n" % (float(time.time()-start_time), pkt.head.seqno, 0, pkt.head.ackno))
		# wait for fin ack
		recvmsg, ad = receiver_socket.recvfrom(1024)
		recvpkt = processMsg(recvmsg)
		log.write("rcv\t\t%f\tFA\t%d\t%d\t%d\n" % (float(time.time()-start_time), recvpkt.head.seqno, 0, recvpkt.head.ackno))
		break
	else: # packet is not FIN
		log.write("rcv\t\t%f\tD\t%d\t%d\t%d\n" % (float(time.time()-start_time), recvpkt.head.seqno, len(data), recvpkt.head.ackno))
		if recvpkt.head.seqno == base_recv: # received the in-order packet
			#data = recvpkt.data
			file.write(data)
			base_recv += len(data)
			next_ack = base_recv
			# check window buffer for packets
			while windows.exist(base_recv) != -1: # more packet with seqno base_recv in buffer
				# pop out and write into file
				idx = windows.exist(base_recv)
				buff_pkt = windows.pop(idx)
				data = buff_pkt.data
				file.write(data)
				# update base_recv
				base_recv += len(data)
				# update next_ack
				next_ack = base_recv
			# send back ACK
			pkt = WinBuffer(Header(next_seq,next_ack,1,0,0))
			receiver_socket.sendto(str(pkt), sender_address)
			log.write("snd\t\t%f\tA\t%d\t%d\t%d\n" % (float(time.time()-start_time), pkt.head.seqno, 0, pkt.head.ackno))
			# test
			if test:
				print "ACK sent with ackno = %s" % str(pkt.head.ackno)
			#next_seq += 1
		elif recvpkt.head.seqno > base_recv: # received out-of-order packet
			windows.push(recvpkt)
			# send back duplicate ACK
			pkt = WinBuffer(Header(next_seq,base_recv,1,0,0))
			receiver_socket.sendto(str(pkt), sender_address)
			log.write("snd\t\t%f\tA\t%d\t%d\t%d\n" % (float(time.time()-start_time), pkt.head.seqno, 0, pkt.head.ackno))
			# test
			if test:
				print "dup ACK sent with ackno = %s" % str(pkt.head.ackno)
		elif recvpkt.head.seqno < base_recv:
			dup_data += 1

total_bytes = lastb - firstb

log.write("\nAmount of Data Received:\t\t\t%d\nNumber of Data Segments Received:\t\t%d\nNumber of duplicate segments received:\t\t%d\n" 
		% (total_bytes, pkt_recv, dup_data))

file.close()
receiver_socket.close()

print "Connection Terminated!!!"