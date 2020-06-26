import uvicorn
from fastapi import FastAPI, Request, Form
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from result import Result, CustomException
from fastapi.responses import JSONResponse
from evaluate_v2 import Evaluator

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key='123')


class EvaluateRequest(BaseModel):
    username: str
    password: str
    content: str
    mode: int


@app.post('/webvpn')
def hello_world(request: Request, username: str=Form(...), password: str=Form(...)):
    evaluator = Evaluator(username)
    evaluator.webvpn_login(username, password)
    webvpn_info = request.session.get('webvpn_info')
    if webvpn_info:
        request.session.pop('webvpn_info')
    request.session.setdefault('webvpn_info', evaluator.session.cookies['wengine_vpn_ticketwebvpn_gdou_edu_cn'])
    return Result.success()


@app.post('/autoEvaluate')
def hello_world(request: Request, args: EvaluateRequest):
    validate(args)
    evaluator = Evaluator(args.username)
    # 设置已登录的webvpn cookie信息
    evaluator.session.cookies['wengine_vpn_ticketwebvpn_gdou_edu_cn'] = request.session.get('webvpn_info')
    evaluator.run(args.username, args.password, args.content, args.mode)
    return Result.success(msg='评价已完成，请到官网查看！')


def validate(args):
    if not args.username or not args.password or not args.content:
        raise CustomException(Result.validate_failed())
    count = 0
    for s in args.content:
        if '\u4e00' <= s <= '\u9fff':
            count += 1
    if count <= 5:
        raise CustomException(Result.validate_failed(msg='必须包含5字以上的评价内容'))


# 自定义异常处理
@app.exception_handler(CustomException)
async def unicorn_exception_handler(request: Request, e: CustomException):
    return JSONResponse(
        status_code=200,
        content=e.result.__dict__,
    )


if __name__ == '__main__':
    uvicorn.run(app='api_v2:app', host='0.0.0.0', port=9802)