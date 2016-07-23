from protocol.router import Router

if __name__ == '__main__':
	bind_ip = '0.0.0.0'
	bind_port = 5881
	max_node_qsize = 200

	router = Router(bind_ip, bind_port, max_node_qsize)
	router.start()
	router.auto_send_find_node()