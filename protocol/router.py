import socket
import logging
from threading import Thread
from binascii import b2a_hex
from collections import deque

from protocol.nodes import Node
from protocol.common import *
from protocol.utils import *
from db.router import RouterDB
from bencodepy import encode, decode

class Router(Thread):
	"""An object for implementing DHT node."""

	# Server

	def auto_find_node(self):
		pass

	def on_message(self, msg, address):
		try:
			pass
		except KeyError:
			pass

	def on_announce_peer(self):
		pass

	def on_get_peers(self):
		pass

	def on_find_node(self):
		pass

	# Client

	def send_get_peers(self):
		pass

	def send_find_node(self, address, nid=None):
		nid = get_neighbor(nid, self.nid) if nid else self.nid
		tid = random_bytes(TID_LENGTH)
		msg = {
			't': tid,
			'y': 'q',
			'q': 'find_node',
			'a': {
				'id': nid,
				'target': random_id()
			}
		}
		self.send_krpc(msg, address)

	def join_network(self):
		if len(self.nodes) == 0:
			for address in BOOTSTRAP_NODES:
				self.send_find_node(address)
		timer(JOIN_NETWORK_INTERVAL, self.join_network)

	# Server/Client

	def send_krpc(self, msg, address):
		try:
			self.sock.sendto(encode(msg), address)
		except Exception:
			pass

	def __init__(self, args):
		self.ip = args['ip']
		self.port = args['port']
		self.max_node = args['max_node']
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.nodes = deque(maxlen=self.max_node)
		self.nid = random_id()

		super().__init__()
		self.logger = logging.getLogger('clue')
		self.sock.bind((self.ip, self.port))
		
	def run(self):
		self.join_network()
		while True:
			try:
				data, address = self.sock.recvfrom(1024)
				msg = decode(data)
				on_message(msg, address)
			except Exception:
				pass