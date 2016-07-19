from threading import Timer

def timer(t, f):
	Timer(t, f).start()