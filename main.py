import argparse
import atexit
import os
import random
import sqlite3
import time
import threading

from flask import Flask, jsonify, session, request, send_from_directory, g
# from flask_session.__init__ import Session

from Herald import Herald

Herald_list = {
    'used': {},
    'available': [],
}

app = Flask(__name__, static_folder='../PTT-web-frontend/build')
# app.secret_key = b'\x1e<d\x14\xbc\x1a\xb1,\x9ck/}\xb7"\xa0\x00'
app.secret_key = os.urandom(32)
# app.config['SESSION_TYPE'] = 'filesystem'
# Session(app)

DATABASE = './user.db'

#######
# args
#######

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=8008)
    parser.add_argument('-d', '--debug', action='store_true', default=False)
    args = parser.parse_args()
    return args

#######
# sqlite3
#######

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
		for idx, value in enumerate(row))

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = make_dicts
    return db

def query_db(query, args=(), one=False, commit=False):
    db = get_db()
    cur = db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    if commit:
        db.commit()
    return (rv[0] if rv else None) if one else rv

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

#######
# session
#######

def get_sess_id():
    if 'user' not in session:
        return None
    id_ = session['user']
    if id_ not in Herald_list['used']:
        session.pop('user', None)
        return None
    return id_

#######
# routings
#######

@app.route('/api/user')
def user():
    id_ = get_sess_id()
    if not id_:
        return {'status': False, 'str': 'haven\'t logged in'}
    print('{} has logged in before'.format(id_))
    user = Herald_list['used'][id_].user
    return {'status': True, 'user': user}

@app.route('/api/login', methods=['POST'])
def login():
    res = request.get_json()
    print('{} login'.format(res['user']))
    id_ = '{}_{}_{}'.format(res['user'], time.time(), random.randint(0, 10000))

    if 'user' in session:
        return {'status': False, 'str': 'Already logged in other tabs.'}

    is_new_thread = False
    herald = None
    try:
        herald = Herald_list['available'].pop()
    except IndexError:
        herald = Herald(id_, res['user'], Herald_list)
        is_new_thread = True
    herald.lock.acquire()
    herald.id = id_

    herald.cond.acquire()
    herald.set_cmd('login', {'user': res['user'], 'pass': res['pass']})
    if is_new_thread:
        herald.thd.start()
    else:
        herald.cond.notify()
    herald.cond.wait()
    status = dict(herald.status)
    herald.clear()
    herald.cond.release()

    if status['status']:
        Herald_list['used'][id_] = herald
        session['user'] = id_
        query_db('INSERT INTO Log (User, SessionId, Action, Timestamp)'
                 ' VALUES (?, ?, ?, ?)', (res['user'], id_, 'login', time.time()), commit=True)
    else:
        Herald_list['available'].append(herald)
    herald.lock.release()

    return status

@app.route('/api/logout')
def logout():
    id_ = get_sess_id()
    if not id_:
        return {'status': False, 'str': 'haven\'t logged in'}
    print('{} logout'.format(id_))
    Herald_list['used'][id_].lock.acquire()
    herald = Herald_list['used'][id_]
    status, _ = herald.send_cmd('logout')
    query_db('INSERT INTO Log (User, SessionId, Action, Timestamp)'
             ' VALUES (?, ?, ?, ?)', (herald.user, id_, 'logout', time.time()), commit=True)
    herald.lock.release()
    session.pop('user', None)
    return status

@app.route('/api/get_board_list')
def get_board_list():
    id_ = get_sess_id()
    if not id_:
        return {'status': False, 'str': 'haven\'t logged in'}
    print('{} get_board_list'.format(id_))
    Herald_list['used'][id_].lock.acquire()
    herald = Herald_list['used'][id_]
    status, data = herald.send_cmd('get_board_list')
    herald.lock.release()
    return {'status': status, 'data': data}

@app.route('/api/get_fav_board')
def get_fav_board():
    id_ = get_sess_id()
    if not id_:
        return {'status': False, 'str': 'haven\'t logged in'}
    print('{} get_fav_board'.format(id_))
    Herald_list['used'][id_].lock.acquire()
    herald = Herald_list['used'][id_]
    status, data = herald.send_cmd('get_fav_board')
    herald.lock.release()
    return {'status': status, 'data': data}

@app.route('/api/get_post', methods=['POST'])
def get_post():
    id_ = get_sess_id()
    if not id_:
        return {'status': False, 'str': 'haven\'t logged in'}
    print('{} get_post'.format(id_))
    res = request.get_json()
    Herald_list['used'][id_].lock.acquire()
    herald = Herald_list['used'][id_]
    status, data = herald.send_cmd('get_post', {
        'board_name': res['board_name'],
        'aid': res['aid']
    })
    herald.lock.release()
    return {'status': status, 'data': data}

@app.route('/api/get_posts', methods=['POST'])
def get_posts():
    id_ = get_sess_id()
    if not id_:
        return {'status': False, 'str': 'haven\'t logged in'}
    print('{} get_posts'.format(id_))
    res = request.get_json()
    Herald_list['used'][id_].lock.acquire()
    herald = Herald_list['used'][id_]
    status, data = herald.send_cmd('get_posts', {
        'board_name': res['board_name'],
        'end_idx': res['end_idx']
    })
    herald.lock.release()
    return {'status': status, 'data': data}

@app.route('/api/get_posts_quick', methods=['POST'])
def get_posts_quick():
    id_ = get_sess_id()
    if not id_:
        return {'status': False, 'str': 'haven\'t logged in'}
    print('{} get_posts_quick'.format(id_))
    res = request.get_json()
    Herald_list['used'][id_].lock.acquire()
    herald = Herald_list['used'][id_]
    status, data = herald.send_cmd('get_posts_quick', {
        'board_name': res['board_name'],
        'end_idx': res['end_idx']
    })
    herald.lock.release()
    return {'status': status, 'data': data}

@app.route('/api/add_push', methods=['POST'])
def add_push():
    id_ = get_sess_id()
    if not id_:
        return {'status': False, 'str': 'haven\'t logged in'}
    print('{} add_push'.format(id_))
    res = request.get_json()
    Herald_list['used'][id_].lock.acquire()
    herald = Herald_list['used'][id_]
    status, data = herald.send_cmd('add_push', {
        'board': res['board'],
        'type': res['type'],
        'content': res['content'],
        'aid': res['aid'],
    })
    herald.lock.release()
    return {'status': status, 'data': data}

@app.route('/api/add_post', methods=['POST'])
def add_post():
    id_ = get_sess_id()
    if not id_:
        return {'status': False, 'str': 'haven\'t logged in'}
    print('{} add_post'.format(id_))
    res = request.get_json()
    Herald_list['used'][id_].lock.acquire()
    herald = Herald_list['used'][id_]
    status, data = herald.send_cmd('add_post', {
        'board': res['board'],
        'category': res['category'],
        'title': res['title'],
        'content': res['content'],
    })
    herald.lock.release()
    return {'status': status, 'data': data}

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
    pass
    print('Logging out all users ...')
    for id_ in list(Herald_list['used'].keys()):
        Herald_list['used'][id_].cond.acquire()
        herald = Herald_list['used'][id_]
        herald.cmd = 'logout'
        herald.timeout = False
        herald.cond.notify()
        herald.cond.wait()
        herald.cond.release()

if __name__ == '__main__':
    args = parse_args()
    app.run(host='0.0.0.0', port=args.port, debug=args.debug)
