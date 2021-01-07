import json
import threading
import time
from json import JSONDecodeError

from redis import Redis

from src import app_logger

import requests
import pickle


class Req:

    def __init__(self):
        self.session = requests.Session()
        self.logger = app_logger.get_logger(__name__)
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0'
        self.headers = {'User-Agent': user_agent, 'Host': 'www.example.com'}
        self.redisClient = Redis(host='localhost')
        self.redisClient.set('cookie', pickle.dumps([]))
        self.p = self.redisClient.pubsub(ignore_subscribe_messages=True)
        threading.Thread(target=self.cookies_loop, args=()).start()

    def set_cookie(self):
        cookies = pickle.loads(self.redisClient.get('cookie'))

        for cookie in cookies:
            self.session.cookies.set(cookie['name'], cookie['value'])



    def cookies_loop(self):
        while True:
            self.set_cookie()
            time.sleep(0.1)

    def post_data_req(self, url, post_data, count=0):

        if count == 2:
            self.logger.error('trouble with cookie')
            return json.dumps({'error': 'selenium error'})

        self.logger.info(url)

        self.logger.debug(post_data)

        try:

            if count == 1:
                self.redisClient.publish('get_cookie', None)
                time.sleep(2)

            data = self.session.post(url, headers=self.headers, data=post_data)

        except Exception as ex:
            self.logger.error(ex)
            return json.dumps({'error': str(ex)})

        if "<noscript>Please enable JavaScript to view the page content.<br/>Your support ID is" in data.text:
            self.logger.info('no js')
            return self.post_data_req(url, post_data, count + 1)

        return data.text

    def get_data_req(self, url, count=0):
        if count == 2:
            self.logger.error('trouble with cookie')
            return json.dumps({'error': 'selenium error'})

        try:

            if count == 1:
                self.redisClient.publish('get_cookie', None)
                time.sleep(2)

            data = self.session.get(url, headers=self.headers)
            self.logger.debug(data.status_code)
        except Exception as ex:
            self.logger.error(ex)
            return json.dumps({'error': str(ex)})

        # 'if it json return'
        try:
            json.loads(data.text)
            return data.text
        except JSONDecodeError:
            pass

        if "<noscript>Please enable JavaScript to view the page content.<br/>Your support ID is" in data.text:
            self.logger.debug('no js get')
            return self.get_data_req(url, count + 1)

        # some error
        if "Vehicle details are not found" in data.text:
            return json.dumps(
                {"error": "Vehicle details are not found. Please see similar vehicles below.", "error_id": 1})

        self.logger.debug(len(data.text))
        return data.text
