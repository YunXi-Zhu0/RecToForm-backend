import requests

class TestForAPI:
    def __init__(self, api_key, base_url, msg):
        self.api_key = api_key
        self.base_url = base_url
        self.msg = msg

    def post(self):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "messages": [
                {
                    "role": "user",
                    "content": self.msg
                }
            ],
            "model": "deepseek-chat",
            "stream": False
        }
        response = requests.post(
                url=self.base_url,
                json=data,
                headers=headers
            )
        result = response.json()
        print(result)

api_key = "<your_api_key>" # https://platform.deepseek.com/api_keys
base_url = "https://api.deepseek.com/chat/completions"
msg = "你好"

tfapi = TestForAPI(api_key, base_url, msg)
tfapi.post()