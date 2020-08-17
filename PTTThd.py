import threading

from PyPtt import PTT

class PTTThd(threading.Thread):
    def __init__(self, herald):
        super(PTTThd, self).__init__(daemon=True)
        self.herald = herald
        self.bot = None
        self.timeout_sec = 70
        self.type_str_to_int = {
            '推': PTT.data_type.push_type.PUSH,
            '→': PTT.data_type.push_type.ARROW,
            '噓': PTT.data_type.push_type.BOO,
        }

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

    # exceptions

    def except_handle(self, e):
        if e == PTT.exceptions.NoSuchUser:
            return '無此使用者'
        # elif e == PTT.exceptions.RequireLogin:
        #     return '使用此 API 前請先登入'
        elif e == PTT.exceptions.NoPermission:
            return '無權限，你可能被水桶或者帳號資格不符'
        elif e == PTT.exceptions.NoFastPush:
            return '此看板不支援快速推文，推文 API 會幫你重推'
        elif e == PTT.exceptions.UserOffline:
            return '使用者離線'
        elif e == PTT.exceptions.ParseError:
            return '此畫面解析錯誤，導致原因可能為傳輸過程中遺失訊息'
        elif e == PTT.exceptions.NoMoney:
            return '沒錢'
        elif e == PTT.exceptions.MoneyTooFew:
            return '錢太少'
        elif e == PTT.exceptions.NoSuchBoard:
            return '沒有這個看板'
        elif e == PTT.exceptions.ConnectionClosed:
            return '連線已經被關閉'
        elif e == PTT.exceptions.UnregisteredUser:
            return '尚未註冊使用者或被退註使用者，因權限受限將無法使用全部功能'
        elif e == PTT.exceptions.MultiThreadOperated:
            return ('一個 PyPtt 物件只能被同一個 thread 操作'
                    '如果有第二個 thread 使用就會跳出此例外')
        elif e == PTT.exceptions.WrongIDorPassword:
            return '帳號密碼錯誤'
        elif e == PTT.exceptions.LoginTooOften:
            return '登入太頻繁'
        elif e == PTT.exceptions.UseTooManyResources:
            return '使用過多 PTT 資源，請稍等一段時間並增加操作之間的時間間隔'
        elif e == PTT.exceptions.HostNotSupport:
            return '批踢踢萬或批踢踢兔不支援這個操作'
        elif e == PTT.exceptions.NoPush:
            return '禁止推文'
        elif e == PTT.exceptions.NoResponse:
            return '禁止回應'
        elif e == PTT.exceptions.NeedModeratorPermission:
            return '需要板主權限'
        elif e == PTT.exceptions.NoSuchPost:
            return '沒有該文章'
        elif e == PTT.exceptions.CanNotUseSearchPostCode:
            return '此狀態下無法使用搜尋文章代碼(AID)功能'
        elif e == PTT.exceptions.UserHasPreviouslyBeenBanned:
            return '使用者之前已被禁言'
        elif e == PTT.exceptions.WrongPassword:
            return '密碼錯誤'
        elif e == PTT.exceptions.NoSearchResult:
            return '沒有搜尋結果'
        else:
            return str(e)

    # cmds

    def cmd_login(self):
        bot = self.bot
        self.herald.clear_status()
        status = self.herald.status

        try:
            bot.login(self.herald.param['user'], self.herald.param['pass'])
            bot.log('登入成功')
            status['status'] = True

            if bot.unregistered_user:
                bot.log('未註冊使用者')
                status['str'] = '未註冊使用者'
                if bot.process_picks != 0:
                    bot.log(f'註冊單處理順位 {bot.process_picks}')
                    status['str'] += f'\n註冊單處理順位 {bot.process_picks}'

            else:
                b_list = bot.get_favourite_board()
                b_list = [b.__dict__ for b in b_list]
                self.herald.data['b_list'] = b_list

        except PTT.exceptions.LoginError:
            bot.log('登入失敗')
            self.herald.set_status(False, '登入失敗')
        except PTT.exceptions.WrongIDorPassword:
            bot.log('帳號密碼錯誤')
            self.herald.set_status(False, '帳號密碼錯誤')
        except PTT.exceptions.LoginTooOften:
            bot.log('請稍等一下再登入')
            self.herald.set_status(False, '請稍等一下再登入')

    def cmd_logout(self):
        self.bot.logout()
        self.herald.set_status(True, '')

    def cmd_get_fav_board(self):
        b_list = self.bot.get_favourite_board()
        b_list = [b.__dict__ for b in b_list]
        self.herald.set_status(True, '')
        self.herald.data['b_list'] = b_list

    def cmd_get_board_list(self):
        b_list = self.bot.get_board_list()
        self.herald.set_status(True, '')
        self.herald.data['b_list'] = b_list

    def cmd_get_post(self):
        b_name = self.herald.param['board_name']
        aid = self.herald.param['aid']
        post = self.bot.get_post(b_name, post_aid=aid)
        post = post.__dict__
        post['push_list'] = [push.__dict__ for push in post['push_list']]

        self.herald.clear_status()
        self.herald.status['status'] = True
        self.herald.data['post'] = post

    def cmd_get_posts(self, quick=False):
        b_name = self.herald.param['board_name']
        end_idx = self.herald.param['end_idx']
        if end_idx == 'recent':
            end_idx = self.bot.get_newest_index(PTT.data_type.index_type.BBS, board=b_name)
        posts = self.get_posts(b_name, end_idx, quick)

        self.herald.clear_status()
        self.herald.status['status'] = True
        self.herald.data['posts'] = posts

    def cmd_push(self):
        board = self.herald.param['board']
        type_ = self.type_str_to_int[self.herald.param['type']]
        content = self.herald.param['content']
        aid = self.herald.param['aid']
        self.bot.push(board, type_, content, post_aid=aid)
        self.herald.set_status(True, '推文完成')

    # run

    def run(self):
        self.bot = PTT.API()
        herald = self.herald
        cond = herald.cond
        cond.acquire()
        while True:
            # try to login
            while herald.cmd != 'login':
                herald.set_status(False, 'Please login first')
                cond.notify()
                cond.wait()
            self.cmd_login()
            cond.notify()
            if herald.status['status']: # if login successfully
                herald.timeout = True
                cond.wait(self.timeout_sec)

                already_logout = False
                while herald.cmd != 'logout' and not herald.timeout:
                    try:
                        if herald.cmd == 'get_fav_board':
                            self.cmd_get_fav_board()
                        elif herald.cmd == 'get_board_list':
                            self.cmd_get_board_list()
                        elif herald.cmd == 'get_post':
                            self.cmd_get_post()
                        elif herald.cmd == 'get_posts':
                            self.cmd_get_posts()
                        elif herald.cmd == 'get_posts_quick':
                            self.cmd_get_posts(quick=True)
                        elif herald.cmd == 'push':
                            self.cmd_push()
                        # add other PTT commands here
                        else:
                            herald.set_status(False, 'No this command')
                    except Exception as e:
                        e_str = self.except_handle(e)
                        self.bot.log('[except]' + e_str)
                        herald.set_status(False, e_str)
                        if e in [PTT.exceptions.LoginError,
                                 PTT.exceptions.NoSuchUser,
                                 # PTT.exceptions.RequireLogin,
                                 PTT.exceptions.UserOffline,
                                 PTT.exceptions.ConnectionClosed,
                                 PTT.exceptions.UnregisteredUser,
                                 PTT.exceptions.WrongIDorPassword,
                                 PTT.exceptions.LoginTooOften,
                                 PTT.exceptions.WrongPassword]:
                            herald['need_relogin'] = True
                            already_logout = True
                            break
                    herald.timeout = True
                    cond.notify()
                    cond.wait(self.timeout_sec)
                if not already_logout:
                    try:
                        self.cmd_logout()
                    except Exception as e:
                        e_str = self.except_handle(e)
                        self.bot.log('[except]' + e_str)
                        herald.set_status(False, e_str)
                herald.glb_list['used'].pop(herald.id, None)
                herald.glb_list['available'].append(herald)
                if not herald.timeout:
                    cond.notify()
            # wait for another login
            cond.wait()
        cond.notify()
        cond.release()
