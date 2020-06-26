from result_status_em import Status


class Result:
    code: int
    msg: str
    data: dict

    def __init__(self, code, msg, data):
        self.code = code
        self.msg = msg
        self.data = data

    @staticmethod
    def success(msg=Status.SUCCESS.get_msg(), data=None):
        return Result(Status.SUCCESS.get_code(), msg, data)

    @staticmethod
    def failed(code=Status.FAILED.get_code(), msg=Status.FAILED.get_msg()):
        return Result(code, msg, None)

    @staticmethod
    def validate_failed(msg=Status.VALIDATE_FAILED.get_msg()):
        return Result(Status.VALIDATE_FAILED.get_code(), msg, None)

    @staticmethod
    def unauthorized():
        return Result(Status.UNAUTHORIZED.get_code(), Status.UNAUTHORIZED.get_msg(), None)

    @staticmethod
    def forbidden():
        return Result(Status.FORBIDDEN.get_code(), Status.FORBIDDEN.get_msg(), None)


class CustomException(Exception):
    def __init__(self, result):
        self.result = result
