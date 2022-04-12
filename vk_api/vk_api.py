import requests
import json

class VkApi:
    def __init__(self, token, version):
        self.ACCESS_TOKEN = token
        self.API_VERSION = version
        self.API_ENDPOINT = "https://api.vk.com/method/"
    
    def method(self, method, params={}):
        params['access_token'] = self.ACCESS_TOKEN
        params['v'] = self.API_VERSION
        url = self.API_ENDPOINT + method
        return json.loads(requests.get(url=url, params=params).text)