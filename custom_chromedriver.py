import urllib.request
import warnings

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common.exceptions import SessionNotCreatedException, WebDriverException, JavascriptException
import requests
import bs4 as bs
import os
from sys import platform
from zipfile import ZipFile
from pynput.keyboard import Key, Controller
from datetime import datetime


class Browser(WebDriver):

    def __init__(self, *args, **kwargs):
        super(Browser, self).__init__(*args, **kwargs)
        self.viewport = self.get_viewport()

    def scroll_to_bottom(self):
        try:
            self.driver.execute_script(
                'var pageHeight = document.querySelector("html").scrollHeight; '
                'window.scrollBy(0, pageHeight);'
            )
        except (JavascriptException, UnexpectedAlertPresentException):
            warnings.warn('Could not scroll to bottom', UserWarning)

    def scroll_to_top(self):
        try:
            self.execute_script(f'window.scrollTo(0, 0)')
        except (JavascriptException, UnexpectedAlertPresentException):
            warnings.warn('Could not scroll to top', UserWarning)

    def get_pageheight(self):
        self.scroll_to_bottom()
        time.sleep(1)
        self.scroll_to_top()
        time.sleep(1)
        try:
            return driver.execute_script(
                'var pageHeight = document.querySelector("html").scrollHeight; '
                'return pageHeight;'
            )
        except (JavascriptException, UnexpectedAlertPresentException):
            warnings.warn('Could not scroll to top', UserWarning)
            return None

    def open_dev_tools(self):
        keyboard = Controller()
        keyboard.press(Key.f12)
        keyboard.release(Key.f12)

    def datalayer(self):
        return self.execute_script('return dataLayer;')

    def get_timed(self, url):
        start = datetime.now().timestamp()
        self.get(url)
        stop = datetime.now().timestamp()
        print(f'Page {url} took {round(stop - start, 2)}s to load.')
        return [url, round(stop - start, 2)]


def browser(maximize=False, user_agent=None, headless=False, incognito=False, size=(1920, 1080)):
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
                     'incognito',
                     f'--window-size={size[0]},{size[1]}']

    for index, value in enumerate([maximize, user_agent, headless, incognito, size]):
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
    if os.path.exists("chromedriver.exe"):
        os.remove("chromedriver.exe")
        print("Updating ChromeDriver..")
    chrome_url = requests.get('https://chromedriver.chromium.org/')
    soup = bs.BeautifulSoup(chrome_url.content, 'lxml')

    all_li = soup.find_all('li')
    for li in all_li:
        if "Latest stable" in li.text:
            if platform in ['win32', 'cygwin']:
                op_sys = 'win32'
            elif platform == 'darwin':
                op_sys = 'mac64'
            elif platform == 'linux':
                op_sys = 'mac64'
            else:
                op_sys = 'win32'
            download_url = f"https://chromedriver.storage.googleapis.com/{li.find('a')['href'].split('?path=')[1]}chromedriver_{op_sys}.zip"
            dir_path = os.path.dirname(os.path.realpath(__file__))
            urllib.request.urlretrieve(download_url, f"{dir_path}\\chromedriver.zip")
    with ZipFile('chromedriver.zip', 'r') as zipObj:
        zipObj.extract('chromedriver.exe')
    print('ChromeDriver successfully installed')
    if os.path.exists('chromedriver.zip'):
        os.remove('chromedriver.zip')
