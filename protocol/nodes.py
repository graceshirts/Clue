from socket import inet_ntoa
from struct import unpack
from protocol.utils import *

class Node(object):
	"""An object for storing node's information."""

	def __init__(self, args):
		self.nid = args['nid']
		self.ip = args['ip']
		self.port = args['port']

	@staticmethod
	def decode(nodes):
		n = []
		length = len(nodes)
		if (length % 26) != 0:
			return n

		for i in range(0, length, 26):
			nid = nodes[i:i+20]
			ip = inet_ntoa(nodes[i+20:i+24])
			port = unpack('!H', nodes[i+24:i+26])[0]
			n.append((nid, ip, port))

		return n