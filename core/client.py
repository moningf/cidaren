import requests
class HttpClient:
    def __init__(self, base_url,token=None, timeout=30):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.timeout = timeout
        if token:
            self.session.headers["UserToken"] = token


    def get(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint, data=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.post(url, json=data, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def set_token(self, token: str):
        self.session.headers["UserToken"] = token


if __name__ == "__main__":
    ## Example usage
    client = HttpClient(base_url="https://app.vocabgo.com/student/api", token="your_token_here")
    response = client.post("/Student/ClassTask/PageTask", {})
    # print(response["data"]["records"][0]["task_name"])
    # print(f"Length: {len(response['data']['records'])}")