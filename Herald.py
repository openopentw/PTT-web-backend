import threading

from PTTThd import PTTThd

class Herald():
    def __init__(self, id_, user, glb_list):
        self.id = id_
        self.user = user
        self.glb_list = glb_list

        self.lock = threading.Lock() # only one request can use this herald at the same time
        self.cond = threading.Condition() # lock between main and thread
        self.thd = PTTThd(self)

        # main -> thread
        self.cmd = ''
        self.param = {}

        # main <- thread
        self.status = {'status': False, 'str': ''}
        self.data = {}

        self.timeout = True

    # set cmd / param (main -> thread)

    def send_cmd(self, cmd, param=None):
        self.cond.acquire()
        self.set_cmd(cmd, param)
        self.cond.notify()
        self.cond.wait()
        status = dict(self.status)
        data = dict(self.data)
        self.cond.release()
        return status, data

    def set_cmd(self, cmd, param=None):
        self.clear()
        self.cmd = cmd
        if param:
            self.param.update(param)
        self.timeout = False

    # set status / data (main <- thread)

    def set_status(self, status, str_):
        self.status.clear()
        self.status['status'] = status
        self.status['str'] = str_

    def clear_status(self):
        self.set_status(False, '')

    # clear all

    def clear(self):
        self.id_ = ''
        # main -> thread
        self.cmd = ''
        self.param.clear()
        # main <- thread
        self.clear_status()
        self.data.clear()
        # timeout
        self.timeout = False
