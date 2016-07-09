from random import randint
from hashlib import sha1
from threading import Timer
from socket import inet_ntoa
from struct import unpack

def generate_chars(length):
	b = ''.join( chr( randint(0, 255) ) for n in range(length) )
	return b

def generate_nid():
	b = generate_chars(length=20)
	h = sha1()
	h.update(b.encode('utf8'))
	return h.digest()

def get_neighbor(target, nid, end=10):
	return target[:end]+nid[end:]

def decode_nodes(nodes):
	n = []
	length = len(nodes)
	if (length % 26) != 0:
		return n

	for i in range(0, length, 26):
		nid = nodes[i:i+20]
		ip = inet_ntoa(nodes[i+20:i+24])
		port = unpack("!H", nodes[i+24:i+26])[0]
		n.append((nid, ip, port))

	return n

def timer(t, f):
	Timer(t, f).start()