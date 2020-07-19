import threading

from PTTThd import PTTThd

class PTTData():
    def __init__(self, id_, glb_list):
        self.id = id_
        self.glb_list = glb_list

        self.lock = threading.Lock()
        self.cond = threading.Condition()
        self.thd = PTTThd(self)

        # main -> thread
        self.cmd = ''
        self.param = {}

        # main <- thread
        self.status = {'status': False, 'str': ''}
        self.data = {}

        self.timeout = True

    # set cmd / param (main -> thread)

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
