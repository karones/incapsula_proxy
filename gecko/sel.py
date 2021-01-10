import pickle
import platform
import threading
from time import sleep

from pyvirtualdisplay import Display
from redis import Redis
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src import app_logger


class Sel:
    def __init__(self):

        self.lock = threading.Lock()
        self.logger = app_logger.get_logger(__name__)
        self.redisClient = Redis(host='localhost')
        self.p = self.redisClient.pubsub(ignore_subscribe_messages=True)

        self.login_text = "user"
        self.password_text = "password"
        self.name = "name"
        self.createDriver()
        self.cookies = ""
        self.set_auth()

        self.set_timer()

        self.p.subscribe(**{'get_cookie': self.get_data()})

    def createDriver(self):
        if platform.system() == 'Windows':
            self.driver = webdriver.Firefox(executable_path=r'./geckodriver.exe')
        else:
            self.display = Display(visible=0, size=(1600, 1024))
            self.display.start()

            self.driver = webdriver.Firefox(executable_path=r'./geckodriver')

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
        self.set_cookie()

    def set_cookie(self):
        self.redisClient.set('cookie', pickle.dumps(self.driver.get_cookies()))
        self.redisClient.publish('set_cookie', None)

    def set_timer(self):
        self.t = threading.Timer(30.0, self.get_data)
        self.t.start()

    def get_data(self, url="https://www.example.com/MyDashboard/Default"):
        self.set_timer()
        self.logger.info('------------------------------')
        self.logger.info(url)
        try:

            self.driver.get(url)
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.ID, "btnSearchIAAContent"))
                )
            except Exception:
                self.logger.error("Connection error")

            if self.name not in self.driver.page_source:
                self.set_auth()

            self.set_cookie()



        except Exception as ex:
            self.createDriver()
            self.set_auth()
            self.logger.error(ex)


if __name__ == '__main__':
    sel = Sel()
