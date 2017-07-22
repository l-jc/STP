from threading import *
from time import sleep
from time import time
import socket

UPDATE_INTERVAL = 1
HEARTBEAT_INTERVAL = 0.5
ROUTE_UPDATE_INTERVAL = 30
THRESHOLD = 3 # missing consecutive heartbeat messages
print_flag = True
file_flag = False

class Broadcast(Thread):
	def __init__(self,event,socket,name,neighbour_nodes):
		Thread.__init__(self)
		self.stopped = event
		self.socket = socket
		self.neighbour_nodes = neighbour_nodes
		self.name = name
		
	def run(self):
		while not self.stopped.wait(UPDATE_INTERVAL):
			# send neighbouring nodes list to neighbouring nodes
			cpneighbours = self.neighbour_nodes.copy()
			info = ''
			for node in cpneighbours:
				info += node + ' '
				info += str(cpneighbours[node][0]) + ' '
				info += str(cpneighbours[node][1]) + '\t'
			broadcast_msg = "0\n%s\n%s\n%s" % (self.name,str(time()),info)
			for node in cpneighbours:
				port = cpneighbours[node][1]
				addr = ('127.0.0.1', port)
				self.socket.sendto(broadcast_msg, addr)
				# print "Broadcast %s to %s" % (broadcast_msg,addr)
				# print "broadcasting..."
			

			
class Heartbeat(Thread):
	def __init__(self,event,socket,name,neighbour_nodes):
		Thread.__init__(self)
		self.stopped = event
		self.socket = socket
		self.neighbour_nodes = neighbour_nodes
		self.name = name
	
	def run(self):
		while not self.stopped.wait(HEARTBEAT_INTERVAL):
			# send heartbeat message to immediate neighbour
			heartbeat_msg = "1\n%s\n" % self.name
			cpneighbours = self.neighbour_nodes.copy()
			for node in cpneighbours:
				port = cpneighbours[node][1]
				addr = ('127.0.0.1', port)
				self.socket.sendto(heartbeat_msg, addr) 			


class Counter(Thread):
	def __init__(self,event,resets,neighbour_nodes,topology):
		Thread.__init__(self)
		self.neighbour_nodes = neighbour_nodes
		self.stopped = event
		self.resets = resets # a dict {'A':reset event}
		self.counter = {}
		for i in self.neighbour_nodes:
			self.counter[i] = 0
		self.topology = topology
		self.dead = []

	def run(self):
		#print "counter run"
		while not self.stopped.wait(HEARTBEAT_INTERVAL):
			# increase counter
			for i in self.counter:
				self.counter[i] += 1
			# check reset signal
			for i in self.resets:
				if self.resets[i].isSet():
					self.counter[i] = 0
					# print "%s is alive" % (i)
					self.resets[i].clear()
				# detect failed node
				elif self.counter[i] > THRESHOLD:
					self.dead.append(i)
			#print self.dead
			
			for i in self.dead:
				# print "delete %s" % i
				del self.neighbour_nodes[i]
				self.topology.deleteNode(i)
				# print "delete %s" % i
				del self.counter[i]
				del self.resets[i]
				print "delete %s done" % i
				# except KeyError:
					#print "keyerror"
					#continue
			self.dead = []
		# print self.topology.graph

class Router(Thread):
	def __init__(self,event,start_point,graph):
		Thread.__init__(self)
		self.stopped = event
		self.start_point = start_point
		self.graph = graph

	def run(self):
		if file_flag:
			rfile = open("route%s" % self.start_point,'w')
		while not self.stopped.wait(ROUTE_UPDATE_INTERVAL):
			prnt = "route@%s:" % str(time())
			if file_flag:
				rfile.write(prnt+'\n')
			print prnt
			self.visited, self.path = self.graph.dijkstra(self.start_point)
			for dest in self.visited:
				route = []
				cur = dest
				while cur != self.start_point:
					route.append(self.path[cur])
					cur = self.path[cur]
				#print "from %s to %s: " % (self.start_point, dest),
				if print_flag:
					print "least-cost path to node %s: " % dest,
				if file_flag:
					rfile.write("from %s to %s: " % (self.start_point, dest))
				for i in route[::-1]:
					if print_flag:
						print i,
					if file_flag:
						rfile.write(i+'->')
				if print_flag:
					print dest,
					print "and the cost is %f" % self.visited[dest]
				if file_flag:
					rfile.write(dest)
					rfile.write(" least-cost = " + str(self.visited[dest]))
					rfile.write('\n')
		if file_flag:
			rfile.close()


def test():
	"""
	skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	stop_flag = Event()
	broadcast = Broadcast(stop_flag,skt,[('B', 2, 3333), ('D', 1, 5555)])
	heartbeat = Heartbeat(stop_flag,skt,[('B', 2, 3333), ('D', 1, 5555)])
	broadcast.start()
	heartbeat.start()
	sleep(3)
	stop_flag.set()
	skt.close()
	"""
	print "broadcast and heartbeat test finished.\ncounter test starting..."
	neighbour_nodes = {'B':(2,3333),'D':(1,5555)}
	new_stop_flag = Event()
	resets = {}
	for i in neighbour_nodes:
		resets[i[0]] = Event()
	counter = Counter(new_stop_flag,resets,neighbour_nodes)
	counter.start()
	sleep(1)
	try:
		resets['B'].set()
	except:
		pass
	sleep(1)
	try:
		resets['D'].set()
	except:
		pass
	sleep(1)
	print counter.counter
	print counter.neighbour_nodes
	new_stop_flag.set()

if __name__ == '__main__':
	test()
