import time
from datetime import datetime
import requests
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

    def __init__(self, user_id, cookie_key, cookie_value, jsessionid):
        self.user_id = user_id
        # 全局同一会话状态request对象
        self.session = requests.session()
        self.session.cookies.set(cookie_key, cookie_value)
        self.session.cookies.set("JSESSIONID", jsessionid)

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
                if item['tjzt'] != "1":
                    course_list.append(item)
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


def verify_code(code):
    json = requests.get("http://www.starix.top:8020/code/verify?code=%s" % code).json()
    return json['code'] == 200


def user_input():

    code = input("输入验证码: ")

    while not verify_code(code):
        print("验证码无效，请重新输入")
        code = input("输入验证码: ")

    content = input("输入对老师的评价(5个字以上): ")
    while not validate_content(content):
        print("字数不够，请重新输入")
        content = input("输入对老师的评价(5个字以上): ")

    print("提交模式: ")
    print("1. 自动提交  2.手动提交")
    mode = input("选择提交模式(序号): ")
    while mode != "1" and mode != "2":
        print("输入无效，请重新选择")
        mode = input("选择提交模式(序号): ")
    return content, mode


def validate_content(content):
    count = 0
    for s in content:
        if '\u4e00' <= s <= '\u9fff':
            count += 1
    return count > 5


def user_login():
    print("="*100)
    print("将在3s后打开浏览器...")
    print("请在打开的浏览器中登录教务系统，登录完成后，浏览器会自动关闭，然后程序开始自动评价")
    time.sleep(3)
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    browser = webdriver.Chrome(executable_path="chromedriver.exe", options=options)
    browser.get('https://jw.gdou.edu.cn')
    print("等待登录...")
    WebDriverWait(browser, 60 * 60 * 24).until(EC.presence_of_all_elements_located((By.ID, "myDiv1")), message='用户未登录')
    cookies = browser.get_cookies()
    user_id = browser.find_element_by_id("sessionUserKey").get_attribute("value")
    for cookie in cookies:
        if cookie['name'] != "JSESSIONID":
            cookie_key = cookie['name']
            cookie_value = cookie['value']
        else:
            jsessionid = cookie['value']
    print("教务系统登录成功")
    print("="*100)
    browser.quit()
    return user_id, cookie_key, cookie_value, jsessionid


if __name__ == '__main__':
    content, mode = user_input()
    user_id, cookie_key, cookie_value, jsessionid = user_login()
    evaluator = Evaluator(user_id, cookie_key, cookie_value, jsessionid)
    evaluator.start(content, mode)
