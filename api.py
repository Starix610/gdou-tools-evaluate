import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from result import Result, CustomException
from fastapi.responses import JSONResponse
from evaluate_old import Evaluator

app = FastAPI()


# 设置跨域传参
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 设置允许的origins来源
    allow_credentials=True,
    allow_methods=["*"],  # 设置允许跨域的http方法，比如 get、post、put等
    allow_headers=["*"])  # 允许跨域的headers，可以用来鉴别来源等作用


class EvaluateRequest(BaseModel):
    username: str
    password: str
    content: str
    mode: int


@app.post('/autoEvaluate')
def evaluate(args: EvaluateRequest):
    validate(args)
    evaluator = Evaluator(args.username)
    evaluator.start(args.username, args.password, args.content, args.mode)
    if args.mode == 1:
        return Result.success(msg='评价已完成，请到官网查看！')
    return Result.success(msg='所有评价已完成并保存，请到官网手动提交！')


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
        status_code=200,  # 抛出的自定义异常采用自己的状态码，但http状态码仍然使用200
        content=e.result.__dict__,
    )


if __name__ == '__main__':
    uvicorn.run(app='api:app', host='0.0.0.0', port=9802)