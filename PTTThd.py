import threading

from PyPtt import PTT

class PTTThd(threading.Thread):
    def __init__(self, data):
        super(PTTThd, self).__init__(daemon=True)
        self.data = data
        self.bot = None
        self.timeout_sec = 70

    # intermediary api

    def get_posts(self, board_name, end_idx, quick=False, num=30):
        posts = []
        beg_idx = end_idx - num + 1
        print(beg_idx, end_idx)
        self.bot.crawl_board(PTT.data_type.crawl_type.BBS,
                             lambda p, posts=posts: posts.append(p),
                             board_name,
                             start_index=beg_idx,
                             end_index=end_idx,
                             query=quick)

        ret = []
        for p in posts:
            p.__dict__['push_list'] = [push.__dict__ for push in p.__dict__['push_list']]
            ret.append(p.__dict__)
        return ret[::-1]

    # cmds

    def cmd_login(self):
        bot = self.bot
        self.data.clear_status()
        status = self.data.status

        try:
            bot.login(self.data.param['user'], self.data.param['pass'])
            bot.log('登入成功')
            status['status'] = True

            if bot.unregistered_user:
                bot.log('未註冊使用者')
                status['str'] = '未註冊使用者'
                if bot.process_picks != 0:
                    bot.log(f'註冊單處理順位 {bot.process_picks}')
                    status['str'] += f'\n註冊單處理順位 {bot.process_picks}'

            else:
                fav_b = self.bot.get_favourite_board()
                fav_b = [b.__dict__ for b in fav_b]
                self.data.data['fav_b'] = fav_b

        except PTT.exceptions.LoginError:
            bot.log('登入失敗')
            self.data.set_status(False, '登入失敗')
        except PTT.exceptions.WrongIDorPassword:
            bot.log('帳號密碼錯誤')
            self.data.set_status(False, '帳號密碼錯誤')
        except PTT.exceptions.LoginTooOften:
            bot.log('請稍等一下再登入')
            self.data.set_status(False, '請稍等一下再登入')

    def cmd_logout(self):
        self.bot.logout()
        self.data.set_status(True, '')

    def cmd_get_fav_board(self):
        fav_b = self.bot.get_favourite_board()
        fav_b = [b.__dict__ for b in fav_b]
        self.data.set_status(True, '')
        self.data.data['fav_b'] = fav_b

    def cmd_get_post(self):
        b_name = self.data.param['board_name']
        aid = self.data.param['aid']
        post = self.bot.get_post(b_name, post_aid=aid)
        post = post.__dict__
        post['push_list'] = [push.__dict__ for push in post['push_list']]

        self.data.clear_status()
        self.data.status['status'] = True
        self.data.data['post'] = post

    def cmd_get_posts(self, quick=False):
        b_name = self.data.param['board_name']
        end_idx = self.data.param['end_idx']
        if end_idx == 'recent':
            end_idx = self.bot.get_newest_index(PTT.data_type.index_type.BBS, board=b_name)
        posts = self.get_posts(b_name, end_idx, quick)

        self.data.clear_status()
        self.data.status['status'] = True
        self.data.data['posts'] = posts

    # run

    def run(self):
        self.bot = PTT.API()
        data = self.data
        cond = data.cond
        cond.acquire()
        while True:
            # try to login
            while data.cmd != 'login':
                data.set_status(False, 'Please login first')
                cond.notify()
                cond.wait()
            self.cmd_login()
            cond.notify()
            # operations after login
            if data.status['status']: # login successfully
                data.timeout = True
                cond.wait(self.timeout_sec)
                while data.cmd != 'logout' and not data.timeout:
                    if data.cmd == 'get_fav_board':
                        self.cmd_get_fav_board()
                    elif data.cmd == 'get_posts':
                        self.cmd_get_posts()
                    elif data.cmd == 'get_post':
                        self.cmd_get_post()
                    elif data.cmd == 'get_posts_quick':
                        self.cmd_get_posts(quick=True)
                    # TODO: add other PTT commands
                    else:
                        data.set_status(False, 'No this command')
                    data.timeout = True
                    cond.notify()
                    cond.wait(self.timeout_sec)
                self.cmd_logout()
                if data.timeout:
                    data.glb_list['used'][data.id].lock.acquire()
                    cur_data = data.glb_list['used'][data.id]
                    data.glb_list['used'].pop(data.id, None)
                    data.glb_list['available'].append(cur_data)
                    cur_data.clear()
                    cur_data.lock.release()
                else:
                    cond.notify()
            # wait for another login
            cond.wait()
        cond.notify()
        cond.release()
