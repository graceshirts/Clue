from protocol.router import Router

if __name__ == '__main__':
	args = {
		'ip': '127.0.0.1',
		'port': 5000,
		'max_node': 200,
	}
	router = Router(args)
	router.start()