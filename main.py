#!/usr/bin/python3
import argparse
import atexit
import os
import random
import sqlite3
import sys
import threading
import time

from flask import Flask, jsonify, session, request, send_from_directory, g
from pathlib import Path

from Herald import Herald

Herald_list = {
    'used': {},
    'available': [],
}

#######
# args
#######

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='localhost')
    parser.add_argument('-p', '--port', default=5000)
    parser.add_argument('--static', default='./frontend_build')
    parser.add_argument('--database', default='./user.db')
    parser.add_argument('-r', '--redirect_out_err', default=False, action='store_true')
    args = parser.parse_args()
    return args

ARGS = parse_args()

app = Flask(__name__, static_folder=ARGS.static)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.secret_key = os.urandom(32)

#######
# sqlite3
#######

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
		for idx, value in enumerate(row))

def get_db():
    if ARGS.database:
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = sqlite3.connect(ARGS.database)
        db.row_factory = make_dicts
        return db

def query_db(query, args=(), one=False, commit=False, wapp=True):
    if ARGS.database:
        db = None
        if wapp:
            db = get_db()
        else:
            db = sqlite3.connect(ARGS.database)
            db.row_factory = make_dicts
        cur = db.execute(query, args)
        rv = cur.fetchall()
        cur.close()
        if commit:
            db.commit()
        if not wapp:
            db.close()
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

    # if 'user' in session:
    #     return {'status': False, 'str': 'Already logged in other tabs.'}

    is_new_thread = False
    herald = None
    try:
        herald = Herald_list['available'].pop()
    except IndexError:
        herald = Herald(id_, res['user'], Herald_list, query_db)
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
    herald.sql_log()
    herald.cond.release()

    if status['status']:
        Herald_list['used'][id_] = herald
        session['user'] = id_
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

@app.route('/api/prevent_logout')
def prevent_logout():
    id_ = get_sess_id()
    if not id_:
        return {'status': False, 'str': 'haven\'t logged in'}
    print('{} prevent_logout'.format(id_))
    Herald_list['used'][id_].lock.acquire()
    herald = Herald_list['used'][id_]
    status, data = herald.send_cmd('prevent_logout')
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

# @app.route('/api/add_post', methods=['POST'])
# def add_post():
#     id_ = get_sess_id()
#     if not id_:
#         return {'status': False, 'str': 'haven\'t logged in'}
#     print('{} add_post'.format(id_))
#     res = request.get_json()
#     Herald_list['used'][id_].lock.acquire()
#     herald = Herald_list['used'][id_]
#     status, data = herald.send_cmd('add_post', {
#         'board': res['board'],
#         'category': res['category'],
#         'title': res['title'],
#         'content': ('{}\r\n\r\n'
#                     '-----\r\n'
#                     '從 https://140.112.31.150 網頁發送，來自: {}'.format(
#                         res['content'], str(request.access_route[0])
#                     )),
#     })
#     herald.lock.release()
#     return {'status': status, 'data': data}

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
    return
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
    print('Executing main ...')
    if ARGS.redirect_out_err:
        cur_path = Path(__file__)
        sys.stdout = open(cur_path.parent / ARGS.static / 'stdout.log', 'w')
        sys.stderr = open(cur_path.parent / ARGS.static / 'stderr.log', 'w')
    app.run(host=ARGS.host, port=ARGS.port)
