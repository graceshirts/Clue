from threading import Timer
from random import randint
from hashlib import sha1

def timer(t, f):
	Timer(t, f).start()

def random_bytes(length):
	return bytes([randint(0, 255) for x in range(length)])

def random_id():
	sh = sha1()
	sh.update(random_bytes(length=20))
	return sh.digest()

def get_neighbor(target, nid, end=-2):
	return target[:end] + nid[end:]