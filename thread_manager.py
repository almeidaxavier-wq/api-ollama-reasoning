import threading

class ThreadManager(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.threads = []
        self.daemon = True
        self.lock = threading.Lock()

    def run(self):
        # Continuously watch for new threads and start them when appended.
        import time
        while True:
            to_start = None
            with self.lock:
                for thread in self.threads:
                    try:
                        thread.start()
                    except RuntimeError:
                        if not thread.is_alive():
                            self.threads.remove(thread)


