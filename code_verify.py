import base64

import redis
import requests
import rsa


def verify(code):
    json = requests.get("http://localhost:8020/code/verify?code=%s" % code).json()
    return json['code'] == 200


if __name__ == '__main__':
    # r = redis.Redis(host='www.starix.top', port=6379, password="aaa123", decode_responses=True)
    # r.set("test", 1, 60 * 5)
    # print(r.get("test"))
    # print(verify("test"))

    # 将base64解码转为bytes
    b_modulus = base64.b64decode("AOer1Q+EwaWeQi9nbtxv2kctImPoyMmxK/F5RMYoPrXr0P9w4ggdnXDDkQyjrp/8Lym9wRibcAX0zRsJeR9wT/DXK3xN8IrrvFOEZBj0ev4NFh6JHJPqStfB966XX8UYeSgHY/qDVA13JDxrBhU151NUwqs0OCDziE4nOlFqDhPx")
    b_exponent = base64.b64decode("AQAB")
    # 公钥生成,python3从bytes中获取int:int.from_bytes(bstring,'big')
    rsa_key = rsa.PublicKey(int.from_bytes(b_modulus, 'big'), int.from_bytes(b_exponent, 'big'))
    # 利用公钥加密,bytes转为base64编码
    encrypt_password = base64.b64encode(rsa.encrypt("shiwenjie2019".encode(), rsa_key)).decode()
    print(encrypt_password)
