from protocol.router import Router

if __name__ == '__main__':
	args = {
		'ip': '0.0.0.0',
		'port': 5000,
		'max_node': 200,
	}
	router = Router(args)
	router.start()
	router.auto_send_find_node()