import threading
import time

class PeriodicTimedService(threading.Thread):
    def __init__(self, task_function, period):
        super().__init__()
        self.task_function = task_function
        self.period = period
        self.__run = True
        self.i = 0
        self.t0 = time.time()

    def sleep(self):
        self.i += 1
        delta = self.t0 + self.period * self.i - time.time()
        if delta > 0:
            time.sleep(delta)
    
    def run(self):
        self.__run = True
        while self.__run:
            self.task_function()
            self.sleep()
    
    def stop(self):
        self.__run = False