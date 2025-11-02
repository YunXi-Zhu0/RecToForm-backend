import requests

class TestForAPI:
    def __init__(self, api_key, base_url, msg):
        self.api_key = api_key
        self.base_url = base_url
        self.msg = msg

    def post(self):
        headers = {
            "Content-Type": "application/json",
        }
        data = {
            "api_key" : self.api_key,
            "messages" : [
                {"role": "user",
                 "content":  self.msg}
            ],
            "model": "sspu-deepseek-r1-32b"
        }

        response = requests.post(url=self.base_url, json=data, headers=headers)
        print(response.text)

api_key = "<your_api_key>" # https://ds.sspu.edu.cn/platform
base_url = "https://ds.sspu.edu.cn/api/v1/chat/completions"
msg = "你好！"

tfapi = TestForAPI(api_key, base_url, msg)

tfapi.post()
