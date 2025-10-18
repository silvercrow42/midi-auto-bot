import requests
import json

from api import event_bus

session = requests.Session()


class ApiResponseError(BaseException):
    def __init__(self, message, code, response):
        super().__init__(message)
        self.code = code
        self.response = response


def default_response_hook(response, *args, **kwargs):
    if response.status_code != 200:
        raise ApiResponseError(
            response.message,
            response.status_code,
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
        code = res.get('code')
        if code != '200':
            if code == '1000':  # 1000: 以不在如何房间，可以刷成空房间数据
                event_bus.refresh_room_info(None)
            else:
                raise ApiResponseError(
                    res.get('message', 'Business logic error'),
                    code,
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
