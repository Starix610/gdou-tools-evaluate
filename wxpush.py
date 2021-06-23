from wxpusher import WxPusher

# 错误日志微信推送，使用了WxPusher，主要是为方便排查问题，如果不需要可以删除
# 如需使用，需要自己配置下面两个参数， WxPusher文档地址：https://wxpusher.zjiecode.com/docs

push_uid = "xxx"
push_token_exception = "xxx"


def push_log(user_id, msg):
    msg = "[自动评价]\n%s\n%s" % (user_id, msg)
    try:
        WxPusher.send_message(content=msg, uids=[push_uid], token=push_token_exception)
    except Exception as e:
        print("推送微信日志失败")


def push_error_log(user_id, msg):
    msg = "[自动评价异常]\n%s\n%s" % (user_id, msg)
    try:
        WxPusher.send_message(content=msg, uids=[push_uid], token=push_token_exception)
    except Exception as e:
        print("推送微信日志失败")


if __name__ == '__main__':
    push_log("123", "日志信息")