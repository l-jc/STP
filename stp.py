# 2
# stp.py
import sys
import random
import time

test = False # change to output test print statement


class Header:
	def __init__(self,seqno,ackno,ack,syn,fin,mws=-1,mss=-1):
		self.seqno = int(seqno)
		self.ackno = int(ackno)
		self.ack = int(ack)
		self.syn = int(syn)
		self.fin = int(fin)
		self.mss = int(mss)
		self.mws = int(mws)

	def setHeader(self,seqno,ackno,ack,syn,fin,mss=-1,mws=-1):
		self.seqno = int(seqno)
		self.ackno = int(ackno)
		self.ack = int(ack)
		self.syn = int(syn)
		self.fin = int(fin)
		self.mss = int(mss)
		self.mws = int(mws)

	def __str__(self):
		return "%d %d %d %d %d %d %d" % (self.seqno, self.ackno, self.ack, self.syn, self.fin, self.mss, self.mws)


class WinBuffer:
	def __init__(self,head,data=''):
		self.head = head
		self.data = data
		self.state = 'new' # new OR sent OR acked

	def __str__(self):
		return "%s %s" % (str(self.head),self.data)


class Window:
	def __init__(self,size,pdrop,start_time,log):
		self.size = size
		self.win = []
		self.pdrop = pdrop
		self.st = start_time
		self.log = log
		self.sent = 0
		self.droped = 0
		self.rex = 0
		random.seed(int(time.time()))

	def push(self,buff):
		self.win.append(buff)

	def remove(self,seqno): # should have removed all the packets with seqno smaller than seqno
		idx = -1
		for i in self.win:
			if i.head.seqno==seqno:
				idx = self.win.find(i)
		del self.win[idx]

	def ack(self,ackno): # remove all the acked packets from window.
		try:
			while self.win[0].head.seqno < ackno:
				del self.win[0]
		except IndexError:
			pass
		return

	def __str__(self,i=-1):
		s = ""
		if i == -1:
			for x in self.win:
				s += str(x)
				s += '\n'
		else:
			s = str(self.win[i])
		return s

	def isUsable(self):
		for i in self.win:
			if i.state == 'new':
				return True
		return False

	def sendAll(self,sock,addr):
		for i in self.win:
			if i.state == 'new':
				i.state = 'sent'
				if drop(self.pdrop):
					#print "PKT drop.  seqno=%s" % (str(i.head.seqno))
					self.log.write("drop\t\t%f\tD\t%d\t%d\t%d\n" % (float(time.time()-self.st), i.head.seqno, len(i.data), i.head.ackno))
					self.droped += 1
					continue
				sock.sendto(str(i),addr)
				self.sent += 1
				self.log.write("snd\t\t%f\tD\t%d\t%d\t%d\n" % (float(time.time()-self.st), i.head.seqno, len(i.data), i.head.ackno))
				# test 
				if test:
					print "PKT sent.  seqno=%s" % (str(i.head.seqno))
		return

	def sendSmallest(self,sock,addr): # used for retransmission
		for i in self.win:
			if i.state != 'acked':
				i.state = 'sent'
				if drop(self.pdrop):
					#print "PKT drop.  seqno=%s" % (str(i.head.seqno))
					self.log.write("drop\t\t%f\tD\t%d\t%d\t%d\n" % (float(time.time()-self.st), i.head.seqno, len(i.data), i.head.ackno))
					break
				sock.sendto(str(i),addr)
				self.rex += 1
				self.log.write("snd\t\t%f\tD\t%d\t%d\t%d\n" % (float(time.time()-self.st), i.head.seqno, len(i.data), i.head.ackno))
				# test
				if test:
					print "PKT sent.  seqno=%s" % (str(i.head.seqno))
				break
		return

	def isFull(self):
		return len(self.win) >= self.size

	def exist(self,seqno):
		for i in self.win:
			if i.head.seqno == seqno:
				return self.win.index(i)
		return -1

	def pop(self,idx):
		pkt = self.win[idx]
		del self.win[idx]
		return pkt


def retrieve(string):
	elem = string[:string.find(' ')]
	string = string[string.find(' ')+1:]
	return elem, string

def processMsg(s): # process the message received and turn it into header and data
	string = s[:]
	seqno, string = retrieve(string)
	ackno, string = retrieve(string)
	ack, string = retrieve(string)
	syn, string = retrieve(string)
	fin, string = retrieve(string)
	mws, string = retrieve(string)
	mss, string = retrieve(string)
	data = string
	head = Header(seqno,ackno,ack,syn,fin,mss,mws)
	ret = WinBuffer(head,data)
	return ret

def requestConnection(sock,addr,seqno,ackno,mws,mss,start_time,log):
	print "Requesting Connection..."
	# send SYN
	syn_pkt = WinBuffer(Header(seqno,ackno,0,1,0,mws,mss))
	sock.sendto(str(syn_pkt), addr)
	log.write("snd\t\t%f\tS\t%d\t%d\t%d\n" % (float(time.time()-start_time), syn_pkt.head.seqno, 0, syn_pkt.head.ackno))
	if test:
		print "SYN sent: %s" % str(syn_pkt)
	seqno += 1

	# receive SYNACK
	recvmsg, ad = sock.recvfrom(1024)
	recvpkt = processMsg(recvmsg)
	log.write("rcv\t\t%f\tSA\t%d\t%d\t%d\n" % (float(time.time()-start_time), recvpkt.head.seqno, 0, recvpkt.head.ackno))
	ackno = recvpkt.head.seqno + 1

	# send ACK
	ack_pkt = WinBuffer(Header(seqno,ackno,1,0,0))
	sock.sendto(str(ack_pkt), addr)
	log.write("snd\t\t%f\tA\t%d\t%d\t%d\n" % (float(time.time()-start_time), ack_pkt.head.seqno, 0, ack_pkt.head.ackno))
	if test:
		print "ACK sent: %s" % str(ack_pkt)

	print "Connection Established!!!\n\n"
	
	return seqno, ackno

def grantConnection(sock,seqno,ackno,start_time,log):
	print "Waiting for Connection..."
	# receive SYN
	recvmsg, sender_address = sock.recvfrom(1024)
	recvpkt = processMsg(recvmsg)
	log.write("rcv\t\t%f\tS\t%d\t%d\t%d\n" % (float(time.time()-start_time), recvpkt.head.seqno, 0, recvpkt.head.ackno))
	ackno = recvpkt.head.seqno + 1
	mws = recvpkt.head.mws
	mss = recvpkt.head.mss
	
	print "Connection Request Received..."

	# send SYNACK
	synack_pkt = WinBuffer(Header(seqno,ackno,1,1,0))
	sock.sendto(str(synack_pkt), sender_address)
	log.write("snd\t\t%f\tSA\t%d\t%d\t%d\n" % (float(time.time()-start_time), synack_pkt.head.seqno, 0, synack_pkt.head.ackno))
	if test:
		print "SYNACK sent with ackno = %s" % str(synack_pkt.head.ackno)

	# receive ACK
	recvmsg, ad = sock.recvfrom(1024)
	recvpkt = processMsg(recvmsg)
	log.write("rcv\t\t%f\tA\t%d\t%d\t%d\n" % (float(time.time()-start_time), recvpkt.head.seqno, 0, recvpkt.head.ackno))
	seqno += 1

	print "Connection Established!!!\n\n"
	return seqno, ackno, mws, mss, sender_address

def drop(pdrop):
	x = random.random()
	if x < pdrop:
		return True
	else:
		return False

