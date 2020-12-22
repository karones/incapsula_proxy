import json
import platform
import threading
from json import JSONDecodeError
from time import sleep

import requests
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import app_logger


class SEL():
    def __init__(self):

        self.lock = threading.Lock()
        #  self.driver = webdriver.Firefox()
        self.login_text = "user"
        self.password_text = "password"
        self.name = "name"
        self.createDriver()
        self.cookies = ""
        self.s = requests.Session()
        self.logger = app_logger.get_logger(__name__)
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0'

        self.headers = {'User-Agent': user_agent, 'Host': 'www.example.com'}
        self.set_auth()
        self.set_timer()

    def createDriver(self):
        if platform.system() == 'Windows':
            self.driver = webdriver.Firefox(executable_path=r'./geckodriver.exe')
        else:
            self.display = Display(visible=0, size=(1600, 1024))
            self.display.start()
            opts = FirefoxOptions()
            opts.add_argument("--headless")
            self.driver = webdriver.Firefox(executable_path=r'/path/geckodriver', firefox_options=opts)

    def post_data_req(self, url, post_data):

        self.logger.info(url)
        try:
            data = self.s.post(url, headers=self.headers, data=post_data)
        except Exception as ex:
            self.logger.error(ex)
            return ""



        if "<noscript>Please enable JavaScript to view the page content.<br/>Your support ID is" in data.text:
            self.logger.info('no js')
            # self.logger.info(data.text)
            self.get_data()
            return self.post_data_req(url, post_data)


        return data.text

    def set_auth(self):
        url = 'https://www.example.com/Login/LoginPage?ReturnUrl=/MyDashboard/Default'

        self.driver.get(url)
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "txtUserName"))
            )
        except Exception:
            pass
        try:
            login = self.driver.find_element_by_id('txtUserName')
            check = self.driver.find_element_by_id('rememberMe')
            self.driver.execute_script("arguments[0].click();", check)
            password = self.driver.find_element_by_xpath(
                '/html/body/section/main/section/div/div[2]/div[1]/section[1]/div/form/div[2]/div/input')
            login.clear()
            password.clear()
            login.send_keys(self.login_text)
            password.send_keys(self.password_text)
            button = self.driver.find_element_by_xpath(
                '//*[@id="loginpageSection"]/div/div[2]/div[1]/section[1]/div/div[7]/div/button')
            button.location_once_scrolled_into_view
            button.click()
        except Exception as Ex:
            self.logger.error(Ex)
            return self.set_auth()

        sleep(2)
        self.cookies = self.driver.get_cookies()

        for cookie in self.cookies:
            self.s.cookies.set(cookie['name'], cookie['value'])

    def get_data_req(self, url):
        try:
            data = self.s.get(url, headers=self.headers)
            self.logger.debug(data.status_code)
        except Exception as ex:
            self.logger.error(ex)
            return ""
        try:
            js = json.loads(data.text)
            return data.text
        except JSONDecodeError:
            pass


        #if we see incapsula, sending to selenium
        if "<noscript>Please enable JavaScript to view the page content.<br/>Your support ID is" in data.text:
            self.logger.debug('no js get')
            self.get_data(url)
            return self.get_data_req(url)

        if "Vehicle details are not found. Please see similar vehicles below." in data.text:
            return json.dumps(
                {"error": "Vehicle details are not found. Please see similar vehicles below.", "error_id": 1})

        self.logger.debug(len(data.text))
        return data.text

    def set_timer(self):
        self.t = threading.Timer(60.0, self.get_data)
        self.t.start()


    #updating coockie for reqests
    def get_data(self, url="https://www.example.com/MyDashboard/Default"):
        self.set_timer()
        self.logger.info('------------------------------')
        self.logger.info(url)
        try:
            self.lock.acquire()

            self.driver.get(url)
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.ID, "txtUserName"))
                )
            except Exception:
                self.logger.error("Connection error")

            if self.name not in self.driver.page_source:
                self.set_auth()

            self.cookies = self.driver.get_cookies()
            for cookie in self.cookies:
                self.s.cookies.set(cookie['name'], cookie['value'])

            self.lock.release()
        except Exception as ex:
            self.createDriver()
            self.set_auth()
            self.logger.error(ex)

