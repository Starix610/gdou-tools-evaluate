import base64
import time
from datetime import datetime
import requests
import rsa
from bs4 import BeautifulSoup
from wxpusher import WxPusher
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import evaluate_params

push_uid = "UID_RrJlsX3ns3sncf2ZI58UyhliOq9f"
push_token_exception = "AT_p1LPrGqupIvdv29dH1tDPNmJylhWlvyR"

class Evaluator:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/79.0.3945.130 Safari/537.36'
    }
    base_url = 'https://jw.gdou.edu.cn'

    def __init__(self, user_id):
        self.user_id = user_id
        # 全局同一会话状态request对象
        self.session = requests.session()

    def get_course_list(self):
        url = self.base_url + '/xspjgl/xspj_cxXspjIndex.html?doType=query&gnmkdm=N401605'
        data = {
            'queryModel.showCount': 15,
            'queryModel.currentPage': 1,
            'queryModel.sortName': '',
            'queryModel.sortOrder': 'asc',
            'time': 0
        }
        json = self.session.post(url, data=data, headers=self.headers).json()
        total_page = json['totalPage']
        total_count = json['totalCount']
        self.log('当前总课程数: %s' % total_count)
        course_list = []
        for page in range(total_page):
            data['queryModel.currentPage'] = page + 1
            json = self.session.post(url, data=data, headers=self.headers).json()
            course_items = json['items']
            for item in course_items:
                # 筛选未提交的评价
                course_list.append(item)
                # if item['tjzt'] != "1":
                #     course_list.append(item)
        self.log('待评课程数: %s' % len(course_list))
        self.push_log('开始评价\n当前总课程数：%s\n待评课程数: %s' %(total_count, len(course_list)))
        if not course_list:
            self.log('你已经完成所有评价啦，无需再次评价，请到官网查看！')
            self.push_log("已完成所有评价，无需再次评价")
            input("按任意键退出...")
            exit(0)
        return course_list

    def do_evaluate(self, content, mode):
        save_evaluation_url = self.base_url + '/xspjgl/xspj_bcXspj.html?gnmkdm=N401605'
        course_list = self.get_course_list()
        self.log('开始自动评价...')
        for i, course in enumerate(course_list):
            self.log('--->[%s-%s]' % (course['kcmc'], course['xsmc']))
            # 先进入评价详情页获取相关参数，主要是xspfb_id这个参数。当前已评价的情况下需要有这个参数才能正常进行评价内容更新。
            evaluation_detail_url = self.base_url + '/xspjgl/xspj_cxXspjDisplay.html?gnmkdm=N401605'
            param = {
                'jxb_id': course['jxb_id'],
                'kch_id': course['kch_id'],
                'xsdm': course['xsdm'],
                'jgh_id': course['jgh_id'],
                'tjzt': course['tjzt'],
                'pjmbmcb_id': '' if 'pjmbmcb_id' not in course else course['pjmbmcb_id'],
                'sfcjlrjs': course['sfcjlrjs']
            }
            response = self.session.post(evaluation_detail_url, data=param, headers=self.headers)
            data = evaluate_params.get_params(response.text, course, content)
            response = self.session.post(save_evaluation_url, data=data, headers=self.headers)
            if '评价保存成功' in response.text:
                self.log('评价保存成功')
            else:
                self.log('评价保存失败: %s' % eval(response.text))
                self.push_error_log(eval(response.text))
            # 提交所有评价
            if i+1 == len(course_list) and mode == "1":
                self.submit_evaluation(data)
        if mode == "2":
            self.log("所有评价已完成，可到官网手动提交！")
            self.push_log("所有评价已完成，待手动提交")
        input("按任意键退出...")
        exit(0)

    def submit_evaluation(self, data):
        submit_evaluation_url = self.base_url + '/xspjgl/xspj_tjXspj.html?gnmkdm=N401605'
        response = self.session.post(submit_evaluation_url, data=data, headers=self.headers)
        if '整体提交成功' in response.text:
            self.log('所有评价已提交成功！')
            self.push_log("所有评价已提交成功")
        else:
            self.log('评价提交失败: %s' % response.text)
            self.log('请稍后重试或反馈问题到公众号')
            self.push_error_log(response.text)

    def log(self, info):
        print('[%s] [%s] %s' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.user_id, info))

    def push_log(self, msg):
        msg = "[自动评价]\n%s\n%s" % (self.user_id, msg)
        WxPusher.send_message(content=msg, uids=[push_uid], token=push_token_exception)

    def push_error_log(self, msg):
        msg = "[自动评价异常]\n%s\n%s" % (self.user_id, msg)
        WxPusher.send_message(content=msg, uids=[push_uid], token=push_token_exception)

    def start(self, content, mode):
        self.log('content: %s' % content)
        self.log('mode: %s' % mode)
        self.do_evaluate(content, mode)


    def jw_login(self, username, password, cookie_key, cookie_value, jsessionid):
        self.session.cookies.set(cookie_key, cookie_value)
        self.session.cookies.set("JSESSIONID", jsessionid)
        # 获取密码加密公钥需要的参数
        publickey_url = self.base_url + '/xtgl/login_getPublicKey.html'
        publickey = self.session.get(publickey_url, headers=self.headers).json()
        # 将base64解码转为bytes
        b_modulus = base64.b64decode(publickey['modulus'])
        b_exponent = base64.b64decode(publickey['exponent'])
        # 公钥生成,python3从bytes中获取int:int.from_bytes(bstring,'big')
        rsa_key = rsa.PublicKey(int.from_bytes(b_modulus, 'big'), int.from_bytes(b_exponent, 'big'))
        # 利用公钥加密,bytes转为base64编码
        encrypt_password = base64.b64encode(rsa.encrypt(password.encode(), rsa_key)).decode()
        jw_login_url = self.base_url + '/xtgl/login_slogin.html'
        response = self.session.get(jw_login_url, headers=self.headers)
        # 如果当前请求直接进入教务系统首页，说明是已登录状态，无需再登录
        # 当评价执行过程出现异常导致webvpn未正确注销时，相同账号再次登录教务系统就会出现这个情况
        if 'index_initMenu' in response.url:
            self.log('当前教务系统账号已处于登录状态')
            return
        # 获取页面上的csrftoken参数
        soup = BeautifulSoup(response.text, "html.parser")
        csrftoken = soup.find(id="csrftoken").get("value")
        data = {
            'csrftoken': csrftoken,
            'language': 'zh_CN',
            'yhm': username,
            'mm': encrypt_password
        }
        response = self.session.post(jw_login_url, data=data, headers=self.headers)
        print(response.text)
        if '用户名或密码不正确' in response.text:
            self.log('用户名或密码不正确')
            return
        if '请先滑动图片进行验证' in response.text:
            self.log('请先滑动图片进行验证')
            return
        self.log('教务系统登录成功')


def validate_content(content):
    count = 0
    for s in content:
        if '\u4e00' <= s <= '\u9fff':
            count += 1
    return count > 5


if __name__ == '__main__':
    evaluator = Evaluator('201711621427')
    evaluator.jw_login('201711621427', 'shiwenjie2019', 'UqZBpD3n3iPIDwJU', 'v1dlsIWwSDNxu', '443D636E367771F90C1A7D6076EE9DCE')
    evaluator.start('老师挺不错的，让我收获很多', "1")
