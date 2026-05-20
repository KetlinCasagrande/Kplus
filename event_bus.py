import queue

event_queue = queue.Queue()

def emit(event, data=None):
    event_queue.put((event, data))