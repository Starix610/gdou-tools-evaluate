import base64
import time

from bs4 import BeautifulSoup
import requests
import rsa
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/79.0.3945.130 Safari/537.36',
}
# COOKIES = {
#     # 目前访问教务系统需通过学校提供的VPN，即先登录学校的WEB VPN站点，再访问学校的一些系统
#     # 所以Cookie中必须要先有这个webvpn认证的字段，才能访问教务系统。
#     'wengine_vpn_ticket': '3ceae4d68ecf3bd1'
# }

BASE_URL = 'https://webvpn.gdou.edu.cn'
BASE_URL_JW = BASE_URL + '/http/77726476706e69737468656265737421a2a611d2746826012d5fc7f4cc'

SESSION = requests.session()


def webvpn_login():
    webvpn_login_url = BASE_URL + "/do-login?local_login=true"
    data = {
        'auth_type': 'local',
        'username': '201711621427',
        'sms_code': '',
        'password': 'Gdou*100412'
    }
    response = SESSION.post(url=webvpn_login_url, data=data, headers=HEADERS)
    # 按照webvpn页面中js的逻辑，是通过判断js代码中logoutOtherToken这个变量是有值来判断是否已经登录过的
    # 然后决定是否踢掉其它客户端，这个值就是其它客户端登录的Cookie中的wengine_vpn_ticket的值
    # 但是js中这个变量怎么被赋上值的暂时未知，但是至少可以知道它的登录逻辑，方便我们模拟登录
    logout_other_token = re.search("logoutOtherToken = '(.*)'", response.text).group(1)
    if logout_other_token != '':
        # 不为空说明在其他客户端登录过，需要再发一次请求踢掉其它客户端
        print('踢掉已登录的客户端: %s' % logout_other_token)
        webvpn_confirm_login_url = BASE_URL + '/do-confirm-login'
        data = {
            'username': '201711621427',
            'logoutOtherToken': logout_other_token
        }
        response = SESSION.post(webvpn_confirm_login_url, data=data, headers=HEADERS)
    print('WEBVPN登录成功: %s' % SESSION.cookies['wengine_vpn_ticket'])


def webvpn_logout():
    webvpn_logout_url = BASE_URL + '/logout'
    SESSION.get(webvpn_logout_url, headers=HEADERS)
    print('WEBVPN注销成功: %s' % SESSION.cookies['wengine_vpn_ticket'])


def jw_login():
    username = '201711621427'
    password = 'shiwenjie2019'

    # 获取密码加密公钥需要的参数
    publickey_url = BASE_URL_JW + '/xtgl/login_getPublicKey.html'
    publickey = SESSION.get(publickey_url, headers=HEADERS).json()
    # 将base64解码转为bytes
    b_modulus = base64.b64decode(publickey['modulus'])
    b_exponent = base64.b64decode(publickey['exponent'])
    # 公钥生成,python3从bytes中获取int:int.from_bytes(bstring,'big')
    rsa_key = rsa.PublicKey(int.from_bytes(b_modulus, 'big'), int.from_bytes(b_exponent, 'big'))
    # 利用公钥加密,bytes转为base64编码
    encrypt_password = base64.b64encode(rsa.encrypt(password.encode(), rsa_key)).decode()
    print(encrypt_password)
    jw_login_url = BASE_URL_JW + '/xtgl/login_slogin.html'
    response = SESSION.get(jw_login_url, headers=HEADERS)
    # 获取页面上的csrftoken参数
    soup = BeautifulSoup(response.text, "html.parser")
    csrftoken = soup.find(id="csrftoken").get("value")
    data = {
        'csrftoken': csrftoken,
        'yhm': username,
        'mm': encrypt_password
    }
    response = SESSION.post(jw_login_url, data=data, headers=HEADERS)
    print(response.text)


def do_evaluate():
    evalution_url = BASE_URL_JW + '/xspjgl/xspj_cxXspjIndex.html?doType=details&gnmkdm=N401605&layout=default&su' \
                                  '=201711621427'
    save_evalution_url = BASE_URL_JW + '/xspjgl/xspj_bcXspj.html?gnmkdm=N401605&su=201711621427'


    html = open('学生评价.html', 'r', encoding='utf-8')  # 以只读的方式打开本地html文件
    htmlhandle = html.read()
    soup = BeautifulSoup(htmlhandle, "html.parser")
    # tds = soup.find(id='1').find_all('td')
    pj_panel_body = soup.find(attrs={'class': 'panel-body xspj-body'})
    sub_divs = pj_panel_body.find_all(attrs={'class': 'panel-body xspj-body'})
    data = {
        'gnmkdm': 'N401605',
        'su': '201711621427',
        'ztpjbl': pj_panel_body['data-ztpjbl'],
        'jszdpjbl': pj_panel_body['data-jszdpjbl'],
        'xykzpjbl': pj_panel_body['data-xykzpjbl'],
        'jxb_id': pj_panel_body['data-jxb_id'],
        'kch_id': pj_panel_body['data-kch_id'],
        'jgh_id': pj_panel_body['data-jgh_id'],
        'xsdm': pj_panel_body['data-xsdm'],
        'modelList[0].pjmbmcb_id': sub_divs[0]['data-pjmbmcb_id'],
        'modelList[0].pjdxdm': sub_divs[0]['data-pjdxdm'],
    }



def run():
    webvpn_login()
    jw_login()
    # 操作完注销当前登录
    webvpn_logout()


if __name__ == '__main__':
    # run()
    do_evaluate()