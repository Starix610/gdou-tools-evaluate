from enum import Enum


class Status(Enum):
    SUCCESS = (0, '操作成功')
    FAILED = (300, '操作失败')
    VALIDATE_FAILED = (400, '参数检验失败')
    UNAUTHORIZED = (401, '暂未登录或token已经过期')
    FORBIDDEN = (403, '没有相关权限')
    SERVER_ERROR = (500, '服务器异常')

    def __init__(self, code, msg):
        self.code = code
        self.msg = msg

    def get_code(self):
        return self.code

    def get_msg(self):
        return self.msg