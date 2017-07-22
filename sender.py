# 2
# sender.py

import sys
import socket
import random
import time
from stp import *

enable_rand_isn = True # change it to use random ISN
test = False # change to test

total = len(sys.argv)
if total != 9: # wrong input
	print "python sender.py receiver_host_ip receiver_port file.txt MWS MSS timeout pdrop seed\n"
	exit(-1)
else: # read the parameters
	receiver_host_ip = str(sys.argv[1])
	receiver_port = int(sys.argv[2])
	file_name = str(sys.argv[3])
	MWS = int(sys.argv[4])
	MSS = int(sys.argv[5])
	timeout = float(sys.argv[6])
	pdrop = float(sys.argv[7])
	seed = int(sys.argv[8])

#set up udp socket
sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver_address = (receiver_host_ip, receiver_port)

if enable_rand_isn:
	random.seed(seed)
	sender_isn = random.randint(0,0x0000ffff)
	next_seq = sender_isn
	next_ack = 0
else:
	sender_isn = 10
	next_seq = 10
	next_ack = 0

# open log file
log = open("sender_log.txt",'w')
if not log:
	print "Can't create log file."
	exit(-3)

# set up start time
start_time = time.time()

# handshake
next_seq, next_ack = requestConnection(sender_socket,receiver_address,next_seq,next_ack,MWS,MSS,start_time,log)

# SendBase
base_seq = next_seq
firstb = next_seq

# send window.
window = Window(MWS/MSS,pdrop,start_time,log)

# open file
file = open(file_name,'r')
if not file:
	print "No such file or directory."
	exit(-2)


# fill window
for i in range(MWS/MSS):
	chunk = file.read(MSS)
	if not chunk:
		break
	else:
		s_chunk = chunk.decode('ascii')
		pkt = WinBuffer(Header(next_seq,next_ack,0,0,0),s_chunk)
		# update seqno and ackno here
		next_seq += len(s_chunk)
		window.push(pkt)

# send out all available packets in window.
print "Transmitting...\n\n"
window.sendAll(sender_socket, receiver_address)

flag_fin = False
dup_ack = 0
total_dup = 0

# set timeout
sender_socket.settimeout(timeout)

while True:
	try:
		recvmsg, ad = sender_socket.recvfrom(1024)
		recvpkt = processMsg(recvmsg)
		log.write("rcv\t\t%f\tA\t%d\t%d\t%d\n" % (float(time.time()-start_time), recvpkt.head.seqno, 0, recvpkt.head.ackno))
		if recvpkt.head.ackno > base_seq:
			dup_ack = 0
			window.ack(recvpkt.head.ackno)
			base_seq = recvpkt.head.ackno
			# send more
			while not window.isFull():
				chunk = file.read(MSS)
				if not chunk:
					flag_fin = True
					break
				else:
					s_chunk = chunk.decode('ascii')
					pkt = WinBuffer(Header(next_seq,next_ack,0,0,0),s_chunk)
					#next_seq += MSS
					next_seq += len(s_chunk)
					window.push(pkt)

			window.sendAll(sender_socket, receiver_address) # send all available pkts which is the pkt
			if flag_fin and base_seq == next_seq: # make sure that all chunks has been acked and send FIN
				print "Connection Terminating..."
				# send fin
				lastb = next_seq
				pkt = WinBuffer(Header(next_seq,next_ack,0,0,1))
				sender_socket.sendto(str(pkt),receiver_address)
				log.write("snd\t\t%f\tF\t%d\t%d\t%d\n" % (float(time.time()-start_time), pkt.head.seqno, 0, pkt.head.ackno))
				# wait for finack
				finack = False
				while not finack:
					recvmsg, ad = sender_socket.recvfrom(1024)
					recvpkt = processMsg(recvmsg)
					log.write("rcv\t\t%f\tFA\t%d\t%d\t%d\n" % (float(time.time()-start_time), recvpkt.head.seqno, 0, recvpkt.head.ackno))
					finack = recvpkt.head.fin and recvpkt.head.ack
				# wait for fin
				fin = False
				while not fin:
					recvmsg, ad = sender_socket.recvfrom(1024)
					recvpkt = processMsg(recvmsg)
					log.write("rcv\t\t%f\tF\t%d\t%d\t%d\n" % (float(time.time()-start_time), recvpkt.head.seqno, 0, recvpkt.head.ackno))
					fin = recvpkt.head.fin
				# send finack
				pkt = WinBuffer(Header(next_seq,next_ack,1,0,1),'')
				sender_socket.sendto(str(pkt),receiver_address)
				log.write("snd\t\t%f\tFA\t%d\t%d\t%d\n" % (float(time.time()-start_time), pkt.head.seqno, 0, pkt.head.ackno))

				break
		elif recvpkt.head.ackno == base_seq: # received duplicate ack
			# check if duplicate == 3
			dup_ack += 1
			total_dup += 1
			if dup_ack >= 3:
				# retransmit
				if test:
					print "fast retransmission"
				window.sendSmallest(sender_socket,receiver_address)
				dup_ack = 0
			pass
	except socket.timeout:
		window.sendSmallest(sender_socket,receiver_address)
		#print "retransmit",
		continue

pkt_sent = window.sent
pkt_drop = window.droped
pkt_rex = window.rex
total_bytes = lastb - firstb

log.write("\nAmount of Data Transferred:\t\t%d\nNumber of Data Segments Sent:\t\t%d\nNumber of Packets Dropped:\t\t%d\nNumber of Retransmitted Segments:\t%d\nNumber of Duplicate ACKs received:\t%d\n" \
		% (total_bytes, pkt_sent, pkt_drop, pkt_rex, total_dup))

file.close()
sender_socket.close()

print "Connection Terminated!!!"