from utils import *

class Node(object):
	"""An object for storing node's information."""

	def __init__(self, args):
		self.nid = args['nid']
		self.ip = args['ip']
		self.port = args['port']