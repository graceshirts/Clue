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

	def __del__(self):
		self.conn.close()

	def commit(self):
		self.conn.commit()

	def create_hash_record(self, info_hash):
		try:
			self.c.execute('''INSERT OR IGNORE INTO info_hash (hash, create_date, update_date) 
					VALUES (?, ?, ?)''', 
					(
						b2a_hex(info_hash), now_time_string(), now_time_string()
					)
				)
			self.commit()
		except Exception:
			raise

	def update_hash_record(self, info_hash):
		try:
			self.c.execute('''UPDATE info_hash SET update_date = ?, popularity = popularity + 1 WHERE hash = ?''',
					(now_time_string(), info_hash)
				)
			self.commit()
		except Exception:
			raise