from threading import Timer, Thread
import socket
from collections import deque
from time import sleep

from random import randint
from hashlib import sha1
from socket import inet_aton, inet_ntoa
from struct import pack, unpack

from bencodepy import encode, decode
from db.routerdb import RouterDB

import pdb

BOOTSTRAP_NODES =  (
	("router.bittorrent.com", 6881),
	("dht.transmissionbt.com", 6881),
	("router.utorrent.com", 6881)
)

TID_LENGTH = 2
RE_join_DHT_INTERVAL = 3
CLIENT_VERSION = b'LT\x01\x00'
TOKEN_LENGTH = 8

def random_bytes(length):
	return bytes([randint(0, 255) for x in range(0, length)])

def random_id():
	h = sha1()
	h.update(random_bytes(length=32))
	return h.digest()

def fake_neighbor(target, nid, end=-5):
	return target[:end]+nid[end:]

def timer(t, f):
	Timer(t, f).start()

def decode_nodes(nodes):
	n = []
	length = len(nodes)
	if length % 26 != 0:
		return n

	for i in range(0, length, 26):
		nid = nodes[i:i+20]
		ip = inet_ntoa(nodes[i+20:i+24])
		port = unpack('!H', nodes[i+24:i+26])[0]
		n.append((nid, ip, port))

	return n

class Node(object):
	"""An object for storing node's information"""
	def __init__(self, nid, ip, port):
		self.nid = nid
		self.ip = ip
		self.port = port

class FakeNode(Thread):
	"""Create a fake DHT node for searching nodes."""
	def __init__(self, max_node_qsize):
		super().__init__()
		self.nid = random_id()
		self.nodes = deque(maxlen=max_node_qsize)
		self.db = RouterDB()

	def re_join_DHT(self):
		if len(self.nodes) == 0:
			self.join_DHT()
		timer(RE_join_DHT_INTERVAL, self.re_join_DHT)

	def join_DHT(self):
		for address in BOOTSTRAP_NODES:
			self.send_find_node(address)

	def auto_send_find_node(self):
		wait = 1.0 / self.max_node_qsize
		while True:
			try:
				node = self.nodes.popleft()
				self.send_find_node((node.ip, node.port), node.nid)
			except IndexError:
				pass
			sleep(wait)

	def send_find_node(self, address, nid=None):
		nid = fake_neighbor(nid, self.nid) if nid else self.nid
		tid = random_bytes(TID_LENGTH)
		msg = {
			't': tid,
			'y': 'q',
			'q': 'find_node',
			'v': CLIENT_VERSION,
			'a': {
				'id': nid,
				'target': random_id()
			}
		}
		self.send_krpc(msg, address)

	def send_get_peers(self, msg, address):
		pass

	def process_find_node_response(self, msg, address):
		nodes = decode_nodes(msg[b'r'][b'nodes'])
		for node in nodes:
			(nid, ip, port) = node
			if len(nid) != 20:
				continue
			if ip == self.bind_ip:
				continue
			if ip == address[0]:
				continue
			if port < 1 or port > 65535:
				continue
			n = Node(nid, ip, port)
			print((ip, port))
			self.nodes.append(n)

	def send_krpc(self, msg, address):
		msg = encode(msg)
		self.udp.sendto(msg, address)

class Router(FakeNode):
	"""The DHT Server listening on a given ip and port."""
	def __init__(self, bind_ip, bind_port, max_node_qsize):
		super().__init__(max_node_qsize)
		self.bind_ip = bind_ip
		self.bind_port = bind_port
		self.max_node_qsize = max_node_qsize

		self.process_request_actions = {
			b'ping': self.on_ping_request,
			b'get_peers': self.on_get_peers_request,
			b'announce_peer': self.on_announce_peer_request,
		}

		self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		address = (self.bind_ip, self.bind_port)
		self.udp.bind(address)
		self.re_join_DHT()

	def run(self):
		while True:
			try:
				(data, address) = self.udp.recvfrom(65536)
				msg = decode(data)
				self.on_message(msg, address)
			except Exception:
				pass

	def on_message(self, msg, address):
		try:
			if msg[b'y'] == b'r':
				if b'nodes' in msg[b'r']:
					self.process_find_node_response(msg, address)
			elif msg[b'y'] == b'q':
				try:
					self.process_request_actions[msg[b'q']](msg, address)
				except KeyError:
					self.send_error(msg, address)
		except:
			pass

	def on_ping_request(self, msg, address):
		pass

	def on_get_peers_request(self, msg, address):
		try:
			tid = msg[b't']
			nid = msg[b'a'][b'id']
			infohash = msg[b'a'][b'info_hash']
			token = infohash[:TOKEN_LENGTH]
			if len(infohash) != 20:
				self.send_error(msg, address, 201)
			else:
				self.db.create_hash_record(info_hash=infohash)
				self.db.update_hash_record(info_hash=infohash)
				msg = {
					't': tid,
					'y': 'r',
					'v': CLIENT_VERSION,
					'r': {
						'id': fake_neighbor(infohash, self.nid, end=-2),
						'token': token,
						'nodes': ''
					}
				}
				self.send_krpc(msg, address)
		except KeyError:
			pass

	def on_announce_peer_request(self, msg, address):
		
		try:
			tid = msg[b't']
			nid = msg[b'a'][b'id']
			infohash = msg[b'a'][b'info_hash']
			token = msg[b'a'][b'token']

			if token == infohash[:TOKEN_LENGTH]:
				if b'implied_port' in msg[b'a'] and msg[b'a'][b'implied_port'] == 1:
					port = address[1]
				else:
					port = msg[b'a'][b'port']
					if port < 1 or port > 65535:
						return
					print(infohash, (address[0], port))
		except Exception:
			pass
		finally:
			msg = {
				't': tid,
				'y': r,
				'r': {
					'id': fake_neighbor(nid, self.nid)
				}
			}
			self.send_krpc(msg, address)

	def send_error(self, msg, address, code=202):
		try:
			tid = msg[b't']
			error_msg = {
				201: 'Generic Error',
				202: 'Server Error',
				203: 'Protocol Error',
				204: 'Method Unknown'
			}
			msg = {
				't': tid,
				'y': 'e',
				'e': [code, error_msg[code]]
			}
			self.send_krpc(msg, address)
		except KeyError:
			pass

if __name__ == '__main__':
	router = Router('0.0.0.0', 5881, 500)
	router.start()
	router.auto_send_find_node()