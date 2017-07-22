"""
Graph Class
test passed
"""
from thrd import *
from threading import *


class Graph:
	def __init__(self):
		self.graph = {}
		self.num_of_node = len(self.graph)
		
	def updateNodes(self,new_node): # not correct 
		"""
		new_node = {'A':[('B',weight,port),('C',weight,port)]}
		"""
		for node in new_node:
			self.graph[node] = new_node[node]
			
	def deleteNode(self,del_node):
		"""
		del_node = 'A'
		"""
		# print "in deleteNode: %s" % str(self.graph)
		try:
			neighbours = self.graph.pop(del_node)
			# print 'in deleteNode: %s' % str(neighbours)
			for (node,weight,port) in neighbours:
				for i in self.graph[node]:
					if i[0] == del_node:
						self.graph[node].remove(i)
						break
		except KeyError:
			tmp = []
			for node in self.graph:
				cand = self.graph[node]
				for link in cand:
					if link[0] == del_node:
						tmp.append(link)
				for old in tmp:
					cand.remove(old)
				tmp = []
		
	def dijkstra(self,start):
		visited = {start:0}
		path = {}
		nodes = set(self.graph)

		while nodes:
			current = None
			for node in nodes:
				if node in visited:
					if current == None:
						current = node
					elif visited[node] < visited[current]:
						current = node
			if current == None:
				break

			nodes.remove(current)
			current_weight = visited[current]

			for edge in self.graph[current]:
				weight = current_weight + (edge[1])
				if edge[0] not in visited or weight < visited[edge[0]]:
					visited[edge[0]] = weight
					path[edge[0]] = current

		return visited, path
		
# Counter should be add to class Node

class Node:
	def __init__(self,name,port,neighbour_nodes,socket):
		"""
		(name,port,neighbour,socket)
		neighbour_nodes = {neighbouring_node name:(wight,port)}
		"""
		self.topology = Graph()
		self.name = name
		self.port = port
		self.neighbour_nodes = neighbour_nodes

		self.socket = socket
		self.heartbeat_stop_flag = Event()
		self.hearbeat = Heartbeat(self.heartbeat_stop_flag,self.socket,self.name,self.neighbour_nodes)
		self.broadcast_stop_flag = Event()
		self.broadcast = Broadcast(self.broadcast_stop_flag,self.socket,self.name,self.neighbour_nodes)

		self.resets = {}
		for i in neighbour_nodes:
			self.resets[i] = Event()
		self.counter_stop_flag = Event()
		self.counter = Counter(self.counter_stop_flag,self.resets,self.neighbour_nodes,self.topology)

		self.router_stop_flag = Event()
		self.router = Router(self.router_stop_flag,self.name,self.topology)

		dic = {self.name:[]}
		for i in self.neighbour_nodes:
			dic[self.name].append((i,self.neighbour_nodes[i][0],self.neighbour_nodes[i][1]))
		self.update(dic)
	

	def initiateNode(self):
		self.hearbeat.start()
		self.router.start()
		self.broadcast.start()
		self.counter.start()

	def terminateNode(self):
		self.counter_stop_flag.set()
		self.broadcast_stop_flag.set()
		self.heartbeat_stop_flag.set()
		self.router_stop_flag.set()
	
	def update(self,new_node):
		self.topology.updateNodes(new_node)
	
	def delete(self,node):
		for i in self.neighbour_nodes:
			if i[0] == node:
				self.neighbour_nodes.remove(i)
				break
		self.topology.deleteNode(node)

	def shortestPath(self):
		return self.topology.dijkstra(self.name)

	def floodout(self,msg):
		cpneighbours = self.neighbour_nodes
		for node in cpneighbours:
			port = self.neighbour_nodes[node][1]
			addr = ('127.0.0.1', port)
			self.socket.sendto(msg, addr)
		
		
def test():
	neighbour_nodes = {'B':(5,2222),'D':(3,3333)}
	node_name = 'A'
	node_port = 1111
	socket = 0
	node = Node(node_name,node_port,neighbour_nodes,socket)

	node.initiateNode()
	node.update({'B':[('A',5,1111),('C',4,3333)]})
	node.update({'C':[('B',4,2222),('D',4,4444)]})
	node.update({'D':[('A',3,1111),('C',4,3333)]})
	visited, path = node.shortestPath()
	print visited
	print path
	print node.topology.graph
	print node.neighbour_nodes

	sleep(4)

	print node.topology.graph
	print node.neighbour_nodes

	node.terminateNode()
		
if __name__ == '__main__':
	test()
