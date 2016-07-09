import socket
import logging
from threading import Thread
from binascii import b2a_hex
from collections import deque
from time import sleep

from libs.utils import *
from libs.knode import KNode
from bencodepy import encode, decode

UDP_IP = "0.0.0.0"
UDP_PORT = 6881
MAX_NODE_QSIZE = 50
DHT_NODES = (
	("router.bittorrent.com", 6881),
	("dht.transmissionbt.com", 6881),
	("router.utorrent.com", 6881)
)
TID_LENGTH = 2
RE_JOIN_DHT_INTERVAL = 3
TOKEN_LENGTH = 2

class Clue(Thread):
	def __init__(self, udp_ip, udp_port, max_node_qsize):
		super().__init__()
		self.daemon = True
		self.logger = logging.getLogger('clue')

		self.nid = generate_nid()
		self.logger.debug( "nid: {}".format( b2a_hex(self.nid) ) )

		self.nodes = deque(maxlen=max_node_qsize)
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		self.udp_ip = udp_ip
		self.udp_port = udp_port
		self.max_node_qsize = max_node_qsize

		self.process_request_actions = {
			b"get_peers": self.on_get_peers_request,
			b"announce_peer": self.on_announce_peer_request,
		}

		self.sock.bind((self.udp_ip, self.udp_port))

	def run(self):
		self.re_join_DHT()
		while True:
			try:
				data, address = self.sock.recvfrom(65536)
				message = decode(data)
				self.on_message(message, address)
			except Exception as error:
				pass

	def on_message(self, message, address):
		try:
			if message[b"y"] == b"r":
				if b"nodes" in message[b"r"]:
					self.find_node_response(message, address)
			elif message[b"y"] == b"q":
				try:
					self.process_request_actions[message[b"q"]](message, address)
				except KeyError:
					self.play_dead(message, address)
		except Exception as error:
			pass

	def send_krpc(self, message, address):
		try:
			self.sock.sendto(encode(message), address)
		except Exception as error:
			self.logger.error("send_krpc: {}".format(error))

	def find_node(self, address, nid=None):
		nid = get_neighbor(nid, self.nid) if nid else self.nid
		tid = generate_chars(TID_LENGTH)
		message = {
			"t": tid,
			"y": "q",
			"q": "find_node",
			"a": {
				"id": nid,
				"target": generate_nid()
			}
		}
		self.send_krpc(message, address)
		self.logger.debug(
			"find_node: \nid: {}\ntg: {}".format(
				b2a_hex( message["a"]["id"] ), 
				b2a_hex( message["a"]["target"] )
			)
		)

	def find_node_response(self, message, address):
		nodes = decode_nodes( message[b"r"][b"nodes"] )
		for node in nodes:
			(nid, ip, port) = node
			if len(nid) != 20: continue
			if ip == self.udp_ip: continue
			if port < 1 or port > 65535: continue
			n = KNode(nid, ip, port)
			self.nodes.append(n)
			self.logger.debug(
				"find_node_response: \nnid: {}\nip: {}\nport: {}".format(
					b2a_hex(nid), ip, port
				)
			)


	def join_DHT(self):
		for address in DHT_NODES:
			self.find_node(address)

	def re_join_DHT(self):
		if len(self.nodes) == 0:
			self.join_DHT()
		timer(RE_JOIN_DHT_INTERVAL, self.re_join_DHT)

	def auto_find_node(self):
		wait = 1.0 / self.max_node_qsize
		while True:
			try:
				node = self.nodes.popleft()
				self.find_node((node.ip, node.port), node.nid)
			except IndexError:
				pass
			sleep(wait)

	def play_dead(self, message, address):
		pass

	def on_get_peers_request(self, message, address):
		try:
			infohash = message[b"a"][b"info_hash"]
			tid = message[b"t"]
			nid = message[b"a"][b"id"]
			token = infohash[:TOKEN_LENGTH]
			message = {
				"t": tid,
				"y": "r",
				"r": {
					"id": get_neighbor(infohash, self.nid),
					"nodes": "",
					"token": token
				}
			}
			self.send_krpc(message, address)
			self.logger.info(
				"on_get_peers_request:\nnid: {}\ninfohash: {}\ntoken {}".format(
					b2a_hex(nid), b2a_hex(infohash), b2a_hex(token)
				)
			)
		except KeyError:
			pass

	def on_announce_peer_request(self, message, address):
		try:
			infohash = message[b"a"][b"info_hash"]
			token = message[b"a"][b"token"]
			nid = message[b"a"][b"id"]
			tid = message[b"t"]

			if infohash[:TOKEN_LENGTH] == token:
				if b"implied_port" in message[b"a"] and message[b"a"][b"implied_port"] != b"0":
					port = address[1]
				else:
					port = int(message[b"a"][b"port"])
					if port < 1 or port > 65535: return
				self.logger.warning(b2a_hex(infohash))
		except Exception:
			pass
		finally:
			self.ok(message, address)

	def ok(self, message, address):
		try:
			tid = message[b"t"]
			nid = message[b"a"][b"id"]
			message = {
				"t": tid,
				"y": "r",
				"r": {
					"id": get_neighbor(nid, self.nid)
				}
			}
			self.send_krpc(message, address)
		except KeyError:
			pass

if __name__ == "__main__":
	logging.basicConfig(filename='log.log', level=logging.WARNING)
	clue = Clue(UDP_IP, UDP_PORT, MAX_NODE_QSIZE)
	logging.debug("initialized.")
	clue.start()
	logging.debug("started.")

	thread = Thread(target=clue.auto_find_node)
	thread.daemon = True
	thread.start()
	logging.debug("auto_find_node_thread started.")

	while True:
		i = input()
		if i == 'q':
			quit()