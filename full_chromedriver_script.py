import pathlib
import random
import sqlite3
import time
import urllib.request
import warnings
import pandas as pd
import requests
import bs4 as bs
import os
from functools import lru_cache
from typing import Union, Any
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common.exceptions import SessionNotCreatedException, WebDriverException, JavascriptException, \
    UnexpectedAlertPresentException, NoSuchElementException, InvalidSelectorException, InvalidArgumentException
from selenium.webdriver.remote.webelement import WebElement
from sys import platform
from zipfile import ZipFile
from pynput.keyboard import Key, Controller
from datetime import datetime, timedelta


DIRNAME = str(pathlib.Path().resolve())
DIRNAME_ORIGIN = os.path.dirname(os.path.realpath(__file__))
DIRNAME_SCREENSHOTS = f'{DIRNAME_ORIGIN}\\screenshots'


def error_handling(func) -> Any:
    '''
    Wrapper function for handling errors in JavaScript execution
    '''
    def wrapper(*args, **kwargs):
        try:
            val = func(*args, **kwargs)
            return val
        except (JavascriptException, UnexpectedAlertPresentException) as e:
            func_name = func.__name__.replace('_', ' ')
            warnings.warn(f'Could not {func_name} because of {e.__class__.__name__} - {e}', UserWarning)
        except (InvalidSelectorException, NoSuchElementException) as e:
            func_name = func.__name__.replace('_', ' ')
            warnings.warn(f'Could not {func_name} because element doesn\'t exist or given selector is not valid\n'
                          f' {e.__class__.__name__} - {e}', UserWarning)
        except InvalidArgumentException as e:
            warnings.warn(f'Could not retrieve url because it probably doesn\'t exist\n'
                          f'{e.__class__.__name__} - {e}', UserWarning)

    return wrapper


class Browser(WebDriver):
    '''
    Subclass of selenium.webdriver.chrome.webdriver.WebDriver
    '''
    def __init__(self, *args, **kwargs):
        super(Browser, self).__init__(*args, **kwargs)
        self.kwargs = kwargs
        self.options = self.kwargs['options']

    @error_handling
    def safe_get(self, url, not_found_selector=None, not_found_substring=None, sleep=1):
        '''
        Funtion to retrieve url with built-in error handling
        '''
        self.get(url)
        time.sleep(sleep)
        if not_found_selector:
            not_found = self.find_elements_by_css_selector(not_found_selector)
            if not_found_substring in not_found[0].text.strip():
                warnings.warn(f'Page {url} not found', UserWarning)
                return False
        return True

    @error_handling
    def get_element(self, selector, attributes=None, multiple=False) -> Union[list, WebElement, None]:
        '''
        Function to search for element with built-in error handling
        Returns list of WebElements, single WebElement or list of dictionaries for attributes
        '''
        elems = self.find_elements_by_css_selector(selector)
        url = self.current_url
        if type(attributes) in [list, tuple] and elems:
            output = []
            for elem in elems:
                attributes = {'url': url}
                for attribute in attributes:
                    attributes[elem] = elem.get_attribute(attribute)
                output.append(attributes)
            return output
        if multiple:
            return elems
        else:
            try:
                return elems[0]
            except IndexError:
                return None

    def get_full_page_screenshot(self, name=str(datetime.now().timestamp()), ext='png', width=1920, sep_instance=True):
        '''
        Function to create a full page screen shot given a set of parameters and
        saves it in /screenshots in the working directory
        Defaults to operations in seperate Browser instance
        '''
        if not os.path.exists(DIRNAME_SCREENSHOTS):
            os.mkdir(DIRNAME_SCREENSHOTS)

        if sep_instance:
            ss_driver = browser(headless=True, size=(width, 1080))
            ss_driver.get(self.current_url)
            time.sleep(2)
            ss_driver.switch_to.default_content()
            page_height = self.get_pageheight()
            ss_driver.set_window_size(width, page_height)
            ss_driver.save_screenshot(f'{DIRNAME_SCREENSHOTS}\\{name}.{ext}')
            ss_driver.quit()

        else:
            page_height = self.get_pageheight()
            driver_width = self.size[0]
            self.switch_to.default_content()
            self.set_window_size(width, page_height)
            self.save_screenshot(f'{DIRNAME_SCREENSHOTS}\\{name}.{ext}')
            self.set_window_size(driver_width, page_height)

    @error_handling
    def scroll_to_bottom(self):
        self.execute_script(
            'var pageHeight = document.querySelector("html").getBoundingClientRect["bottom"]; '
            'window.scrollBy(0, pageHeight);'
        )

    @error_handling
    def scroll_to_top(self):
        self.execute_script(f'window.scrollTo(0, 0)')

    @error_handling
    def get_pageheight(self) -> int:
        return self.execute_script('var html = document.querySelector(\'html\'); '
                                   'return html.getBoundingClientRect();'
                                   )['bottom']

    def open_dev_tools(self):
        keyboard = Controller()
        keyboard.press(Key.f12)
        keyboard.release(Key.f12)

    @error_handling
    def get_datalayer(self) -> dict:
        return self.execute_script('return dataLayer;')

    def get_timed(self, url, print_val=True) -> list:
        '''
        Retrieves given url and returns its load time in a [url, time_to_load] format
        '''
        start = datetime.now().timestamp()
        try:
            self.get(url)
        except WebDriverException:
            warnings.warn(f'Page {url} cannot be opened: ')
        stop = datetime.now().timestamp()
        if print_val:
            print(f'Page {url} took {round(stop - start, 2)}s to load.')
        return [url, round(stop - start, 2)]

    @error_handling
    def click_element(self, selector, iframe=False, iframe_selector='iframe'):
        '''
        Function to click an HTML element by its CSS selector
        When element is inside an iframe specify the iframe element by using the params iframe and iframe_selector
        '''
        try:
            if iframe:
                frame = self.find_element_by_css_selector(iframe_selector)
                self.switch_to.frame(frame)
            element = self.find_element_by_css_selector(selector)
            element.click()
            self.switch_to.default_content()

        except NoSuchElementException:
            warnings.warn('Could not click button, element not found in HTML.', UserWarning)


def browser(maximize=False, user_agent=random_ua, headless=False,
            incognito=False, size=(), disable_scrollbar=False) -> Browser:
    '''
    function to initialize Browser object given a set of ChromeOptions and
    to make sure ChromeDriver is properly installed and up to date by calling update_chromedriver() if necessary
    '''
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-notifications')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    d = webdriver.DesiredCapabilities.CHROME
    d['goog:loggingPrefs'] = {'browser': 'ALL'}

    option_values = ['--start-maximized',
                     f'user-agent={user_agent}',
                     '--headless',
                     'incognito'
                     ]
    if size:
        if not type(size) in [list, tuple]:
            raise TypeError(f'The size parameter must be of type "list" or "tuple", not type "{type(size).__name__}".')

        if maximize:
            warnings.warn(
                f'Cannot use maximize and size. Browser will not use maximize. Size is set to {size[0]}x{size[1]}')
        option_values.append(f'--window-size={size[0]},{size[1]}')

    for index, value in enumerate([maximize, user_agent, headless, incognito, size, disable_scrollbar]):
        if value:
            options.add_argument(option_values[index])

    try:
        return Browser(desired_capabilities=d, options=options)
    except (SessionNotCreatedException, WebDriverException):
        update_chromedriver()

        try:
            return Browser(desired_capabilities=d, options=options)
        except WebDriverException:
            raise WebDriverException(
                "Google Chrome not found in PATH, make sure the Google Chrome browser is installed properly.")


def update_chromedriver():
    '''
    Function to retrieve and unpack the latest stable version of ChromeDriver
    '''
    if os.path.exists("chromedriver.exe"):
        os.remove("chromedriver.exe")
        print("Updating ChromeDriver..")
    chrome_url = requests.get('https://chromedriver.chromium.org/')
    soup = bs.BeautifulSoup(chrome_url.content, 'lxml')

    all_li = soup.find_all('li')
    for li in all_li:
        if "Latest stable" in li.text:
            if platform in ['darwin', 'linux']:
                op_sys = 'mac64'
            else:
                op_sys = 'win32'
            download_url = f"https://chromedriver.storage.googleapis.com/{li.find('a')['href'].split('?path=')[1]}chromedriver_{op_sys}.zip"
            file_n = f"{DIRNAME_ORIGIN}\\chromedriver.zip"
            urllib.request.urlretrieve(download_url, file_n)
    with ZipFile(file_n, 'r') as zipObj:
        zipObj.extract('chromedriver.exe')
    print('ChromeDriver successfully installed')
    if os.path.exists(file_n):
        os.remove(file_n)


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
        results.append({'device': device, 'ua_string': ua})
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
