import os
import socket
import logging
from threading import Thread
from binascii import b2a_hex
from collections import deque
from time import sleep

from protocol.nodes import Node
from protocol.common import *
from protocol.utils import *
from db.router import RouterDB
from bencodepy import encode, decode

from pdb import set_trace as bkp

class Router(Thread):
	"""An object for implementing DHT node."""

	# Server

	def auto_send_find_node(self):
		wait = 1.0 / self.max_node
		while True:
			try:
				node = self.nodes.popleft()
				self.send_find_node((node.ip, node.port), node.nid)
			except IndexError:
				pass
			try:
				sleep(wait)
			except KeyboardInterrupt:
				os._exit(0)


	def on_find_node_response(self, msg, address):
		nodes = Node.decode(msg[b'r'][b'nodes'])
		for node in nodes:
			(nid, ip, port) = node
			if len(nid) != 20: continue
			if ip == self.ip: continue
			args = {
				'nid': nid,
				'ip': ip,
				'port': port
			}
			n = Node(args)
			self.nodes.append(n)

	def on_message(self, msg, address):
		try:
			_type = msg[b'y']
			if _type == b'r':
				if b'nodes' in msg[b'r']:
					self.on_find_node_response(msg, address)
		except KeyError:
			pass

	def on_announce_peer(self):
		pass

	def on_get_peers(self):
		pass

	def on_find_node(self):
		pass

	def on_ping(self):
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
		super().__init__()
		self.ip = args['ip']
		self.port = args['port']
		self.max_node = args['max_node']
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.nodes = deque(maxlen=self.max_node)
		self.nid = random_id()

		self.sock.bind((self.ip, self.port))
		
		self.join_network()

	def run(self):
		while True:
			try:
				(data, address) = self.sock.recvfrom(65536)
				msg = decode(data)
				self.on_message(msg, address)
			except Exception:
				pass