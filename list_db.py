import sqlite3

import pandas as pd

DATABASE = './user.db'

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
		for idx, value in enumerate(row))

def main():
    db = sqlite3.connect(DATABASE)

    # complete log
    print('complete log:')
    df = pd.read_sql_query('SELECT * FROM Log', con=db)
    print(df)

    # find current online user
    print('current user:')
    df = pd.read_sql_query('SELECT SessionId FROM Log WHERE Action="login"', con=db)
    login_list = df['SessionId'].tolist()
    df = pd.read_sql_query('SELECT SessionId FROM Log WHERE Action="logout"', con=db)
    logout_list = df['SessionId'].tolist()
    df = pd.read_sql_query('SELECT SessionId FROM Log WHERE Action="timeout"', con=db)
    timeout_list = df['SessionId'].tolist()
    print([id_ for id_ in login_list if id_ not in logout_list and id_ not in timeout_list])

if __name__ == '__main__':
    main()
