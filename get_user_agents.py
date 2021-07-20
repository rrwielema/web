from functools import lru_cache
import pathlib
from typing import Union

import bs4 as bs
import os
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import requests
import random

DIRNAME = str(pathlib.Path().resolve())


@lru_cache
def check_db(filters) -> list:
    '''
    Function to retrieve user-agents from an existing database.
    Will create a new database if there is none, or if existing data is older than 30 days

    Returns a (filtered - when specified) list of user_agents, possibly cached to maximize speed.
    '''
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
    '''
    Function to retrieve existing databases
    '''
    files = os.listdir(DIRNAME)
    dbs = [f for f in files if 'db_user_agents' in f]
    if len(dbs) == 0:
        return None
    else:
        return dbs[0]


def collect_agents():
    '''
    Function to retrieve the latest user-agents for all different devices and operating systems and
    to create a database to store the results.
    '''
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
    dbs = [f for f in os.listdir(DIRNAME) if 'db_user_agents' in f]
    for x in dbs:
        os.remove(DIRNAME + '\\' + x)

    conn = sqlite3.connect(DIRNAME + '\\' + today + '-db_user_agents.db')
    df.to_sql('user_agents', con=conn, if_exists='replace')
    conn.close()

    return df


def random_ua(device_filter=None, amount=1) -> Union[str, list]:
    '''
    Function to return a random user-agent or a list of random user-agents.
    Possibility to filter for a specific device or operating system.
    '''
    agents = check_db(device_filter)
    if amount == 1:
        return random.choice(agents)
    return random.choices(agents, k=amount)


def list_devices(filter_=None) -> Union[list, None]:
    '''
    Function to list devices that are currently in an existing database
    '''
    db = get_db()

    if db:
        conn = sqlite3.connect(db)
        query = 'SELECT device FROM user_agents'
        if filter_:
            query += f' WHERE device LIKE \'%{filter_}%\''
        df = pd.read_sql(query, con=conn)
        return df['device'].unique().tolist()
    else:
        return
