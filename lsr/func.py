def string2dict(sender,s):
	"""
	s = "C 3 2002\nE 2 2004\n"
	"""
	rt = {}
	rt[sender] = []
	a = s.split('\t')
	for line in a:
		if line != '':
			b = line.split(' ')
			neighbour = b[0]
			weight = float(b[1])
			port = int(b[2])
			rt[sender].append((neighbour,weight,port))
	return rt



def test():
	print string2dict('F',"C 3.0 2002\tE 2.0 2004\t")

if __name__ == '__main__':
	test()
