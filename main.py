import argparse
import atexit
import os
import random
import time
import threading

from flask import Flask, jsonify, session, request, send_from_directory
# from flask_session.__init__ import Session

from PTTData import PTTData

DATA = {
    'used': {},
    'available': [],
}

app = Flask(__name__, static_folder='../PTT-web-frontend/build')
# app.secret_key = b'\x1e<d\x14\xbc\x1a\xb1,\x9ck/}\xb7"\xa0\x00'
app.secret_key = os.urandom(32)
# app.config['SESSION_TYPE'] = 'filesystem'
# Session(app)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=8008)
    parser.add_argument('-d', '--debug', action='store_true', default=False)
    args = parser.parse_args()
    return args

@app.route('/api/user')
def user():
    if 'user' in session:
        print('{} has logged in before'.format(session['user']))
        return {'status': True, 'user': session['user']}
    return {'status': False, 'str': 'haven\'t logged in'}

@app.route('/api/login', methods=['POST'])
def login():
    res = request.get_json()
    print('{} login'.format(res['user']))
    id_ = '{}_{}_{}'.format(res['user'], time.time(), random.randint(0, 10000))

    if 'user' in session:
        return {'status': False, 'str': 'Already logged in other tabs.'}

    is_new_thread = False
    data = None
    try:
        data = DATA['available'].pop()
    except IndexError:
        data = PTTData(id_, DATA)
        is_new_thread = True
    data.lock.acquire()
    data.id = id_

    data.cond.acquire()
    data.set_cmd('login', {'user': res['user'], 'pass': res['pass']})
    if is_new_thread:
        data.thd.start()
    else:
        data.cond.notify()
    data.cond.wait()
    status = dict(data.status)
    data.clear()
    data.cond.release()

    if status['status']:
        DATA['used'][id_] = data
        session['user'] = id_
    else:
        DATA['available'].append(data)
    data.lock.release()

    return status

@app.route('/api/logout')
def logout():
    id_ = session['user']
    print('{} logout'.format(id_))

    DATA['used'][id_].lock.acquire()
    data = DATA['used'][id_]

    data.cond.acquire()
    data.set_cmd('logout')
    data.cond.notify()
    data.cond.wait()
    status = dict(data.status)
    data.clear()
    data.cond.release()

    DATA['used'].pop(id_, None)
    DATA['available'].append(data)
    data.lock.release()

    session.pop('user', None)
    return status

@app.route('/api/get_fav_board')
def get_fav_board():
    id_ = session['user']
    print('{} get_fav_board'.format(id_))

    DATA['used'][id_].lock.acquire()
    data = DATA['used'][id_]

    data.cond.acquire()
    data.set_cmd('get_fav_board')
    data.cond.notify()
    data.cond.wait()
    status = dict(data.status)
    ret_data = dict(data.data)
    data.cond.release()

    data.lock.release()

    return {'status': status, 'data': ret_data}

@app.route('/api/get_post', methods=['POST'])
def get_post():
    id_ = session['user']
    print('{} get_post'.format(id_))
    res = request.get_json()

    DATA['used'][id_].lock.acquire()
    data = DATA['used'][id_]

    data.cond.acquire()
    data.set_cmd('get_post',
                 {'board_name': res['board_name'],
                  'aid': res['aid']})
    data.cond.notify()
    data.cond.wait()
    status = dict(data.status)
    ret_data = dict(data.data)
    data.cond.release()

    data.lock.release()

    return {'status': status, 'data': ret_data}

@app.route('/api/get_posts', methods=['POST'])
def get_posts():
    id_ = session['user']
    print('{} get_posts'.format(id_))
    res = request.get_json()

    DATA['used'][id_].lock.acquire()
    data = DATA['used'][id_]

    data.cond.acquire()
    data.set_cmd('get_posts',
                 {'board_name': res['board_name'],
                  'end_idx': res['end_idx']})
    data.cond.notify()
    data.cond.wait()
    status = dict(data.status)
    ret_data = dict(data.data)
    data.cond.release()

    data.lock.release()

    return {'status': status, 'data': ret_data}

@app.route('/api/get_posts_quick', methods=['POST'])
def get_posts_quick():
    id_ = session['user']
    print('{} get_posts_quick'.format(id_))
    res = request.get_json()

    DATA['used'][id_].lock.acquire()
    data = DATA['used'][id_]

    data.cond.acquire()
    data.set_cmd('get_posts_quick',
                 {'board_name': res['board_name'],
                  'end_idx': res['end_idx']})
    data.cond.notify()
    data.cond.wait()
    status = dict(data.status)
    ret_data = dict(data.data)
    data.cond.release()

    data.lock.release()

    return {'status': status, 'data': ret_data}

@app.route('/api')
def api():
    s = 'Hello, API!'
    return jsonify(s)

# STATIC
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != '' and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

@atexit.register
def logout_all():
    print('Logging out all users ...')
    for id_ in DATA['used']:
        DATA['used'][id_].cond.acquire()
        data = DATA['used'][id_]
        data.cmd = 'logout'
        data.timeout = False
        data.cond.notify()
        data.cond.wait()
        status = dict(data.status)
        data.clear()
        data.cond.release()
        if data.thd.is_alive():
            data.thd.join()
        del DATA['used'][id_]

if __name__ == '__main__':
    args = parse_args()
    app.run(host='0.0.0.0', port=args.port, debug=args.debug)
