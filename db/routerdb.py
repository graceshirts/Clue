import sqlite3
import datetime
from binascii import b2a_hex

import pdb

FILE = 'clue.db'

def now_time_string():
	now = datetime.datetime.now()
	return now.strftime('%d/%m/%Y %H:%M:%S')

class RouterDB(object):
	def __init__(self):
		self.conn = sqlite3.connect(FILE, check_same_thread=False)
		self.c = self.conn.cursor()
		self.c.execute('''VACUUM''')
		self.commit()

	def __del__(self):
		self.conn.close()

	def commit(self):
		self.conn.commit()

	def create_hash_record(self, hash_type, info_hash, node_ip):
		self.c.execute('''INSERT OR REPLACE INTO info_hash (hash, hash_type, create_date, node_ip) 
				VALUES (?, ?, ?, ?)''', 
				(
					b2a_hex(info_hash), hash_type, now_time_string(), node_ip
				)
			)
		self.commit()

	def delete_bans_record(self, node_ip):
		deleted = self.c.execute('''DELETE FROM info_hash WHERE node_ip = ?''', node_ip)
		print('delete malicious record.', deleted)
		self.commit()