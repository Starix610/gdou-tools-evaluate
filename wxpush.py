from wxpusher import WxPusher

push_uid = "UID_RrJlsX3ns3sncf2ZI58UyhliOq9f"
push_token_exception = "AT_p1LPrGqupIvdv29dH1tDPNmJylhWlvyR"


def push_log(content):
    content = "[自动评价]\n%s" % content
    WxPusher.send_message(content=content, uids=[push_uid], token=push_token_exception)


def push_error_log(content):
    content = "[自动评价异常]\n%s" % content
    WxPusher.send_message(content=content, uids=[push_uid], token=push_token_exception)

if __name__ == '__main__':
    input()
    push_log("123")