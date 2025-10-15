import requests
import json

session = requests.Session()


class ApiResponseError(BaseException):
    def __init__(self, message, response):
        super().__init__(message)
        self.response = response


def default_response_hook(response, *args, **kwargs):
    if response.status_code != 200:
        raise ApiResponseError(
            response.message,
            response
        )
    content_type = response.headers.get('Content-Type', '')
    if 'application/json' in content_type:
        try:
            res = response.json()
        except json.JSONDecodeError:
            raise ApiResponseError(
                f"Invalid JSON response: {response.text}",
                response
            )
        if res.get('code') != '200':
            raise ApiResponseError(
                res.get('message', 'Business logic error'),
                response
            )
        return response


def get_session():
    from websocket import ws_client
    session.headers.update({
        'X-Client-Id': ws_client.client_id,
    })
    # 添加默认的响应钩子
    session.hooks['response'].append(default_response_hook)
    return session
