from functools import lru_cache
import time

import bs4 as bs
import os
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from html_table_parse import to_dataframe
import requests
import random


@lru_cache
def check_db(filters):
    today = datetime.now()
    db_name = get_db()
    if db_name:
        last_date = datetime.strptime(db_name.split('-')[0], '%Y%m%d')
        if last_date > today - timedelta(days=30):
            conn = sqlite3.connect(db_name)

            query = 'SELECT * FROM user_agents'

            df = pd.read_sql(query, con=conn)
            conn.close()
            if filters:
                df = df[df.device.str.contains(filters)]
            agents = df['ua_string'].unique().tolist()
            return agents

    print('Fetching most recent user agents')
    df = collect_agents()
    if filters:
        agents = df[df.device.str.contains(filters)]['ua_string'].unique().tolist()
    else:
        agents = df['ua_string'].unique().tolist()

    return agents


def get_db():
    files = os.listdir(os.path.dirname(os.path.realpath(__file__)))
    dbs = [f for f in files if 'db_user_agents' in f]
    if len(dbs) == 0:
        return None
    else:
        return dbs[0]


def collect_agents():
    url = 'https://deviceatlas.com/blog/list-of-user-agent-strings'

    r = requests.get(url)
    soup = bs.BeautifulSoup(r.content, 'lxml')
    tables = soup.select('table')
    results = []
    for table in tables:
        device = table.select('th')[0].text
        ua = table.select('td')[0].text
        results.append({'device': device, 'ua_string':ua})
    df = pd.DataFrame(results)

    today = datetime.strftime(datetime.now(), '%Y%m%d')
    dbs = [f for f in os.path.dirname(os.path.realpath(__file__)) if 'db_user_agents' in f]
    for x in dbs:
        os.remove(os.path.dirname(os.path.realpath(__file__)) + '\\' + x)

    conn = sqlite3.connect(today + '-db_user_agents.db')
    df.to_sql('user_agents', con=conn, if_exists='replace')
    conn.close()

    return df


def random_ua(device_filter=None, amount=1):
    agents = check_db(device_filter)
    if amount == 1:
        return random.choice(agents)
    return random.choices(agents, k=amount)


def list_devices(filter=None):
    db = get_db()

    if db:
        conn = sqlite3.connect(db)
        query = 'SELECT device FROM user_agents'
        if filter:
            query += f' WHERE device LIKE \'%{filter}%\''
        df = pd.read_sql(query, con=conn)
        return df['device'].unique().tolist()


