import base64
from datetime import datetime
import requests
import rsa
from bs4 import BeautifulSoup
import evaluate_params
from result import CustomException, Result
import wxpush
from slide_captcha_pass import CaptchaProcessor


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
                if item['tjzt'] != "1":
                    course_list.append(item)
        self.log('待评课程数: %s' % len(course_list))
        wxpush.push_log(self.user_id, '开始评价\n当前总课程数：%s\n待评课程数: %s' % (total_count, len(course_list)))
        if not course_list:
            self.log('已完成所有评价，无需再次评价')
            wxpush.push_log(self.user_id, "已完成所有评价，无需再次评价")
            raise CustomException(Result.failed(msg='你已经完成所有评价啦，无需再次评价，请到官网查看！'))
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
                wxpush.push_error_log(self.user_id, eval(response.text))
            # 提交所有评价
            if i+1 == len(course_list) and mode == 1:
                self.log("即将提交全部评价");
                self.submit_evaluation(data)
        if mode == 2:
            self.log("所有评价已完成，待手动提交")
            wxpush.push_log(self.user_id, "所有评价已完成，待手动提交")

    def submit_evaluation(self, data):
        submit_evaluation_url = self.base_url + '/xspjgl/xspj_tjXspj.html?gnmkdm=N401605'
        response = self.session.post(submit_evaluation_url, data=data, headers=self.headers)
        if '整体提交成功' in response.text:
            self.log('所有评价已提交成功')
            wxpush.push_log(self.user_id, "所有评价已提交成功")
        else:
            self.log('评价提交失败: %s' % response.text)
            wxpush.push_error_log(self.user_id, self.user_id, '评价提交失败: %s' % response.text)
            raise CustomException(Result.failed(msg='评价提交失败，请稍后重试或反馈问题到公众号'))

    def log(self, info):
        print('[%s] [%s] %s' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.user_id, info))

    def start(self, username, password, content, mode, cookies):
        self.log('content: %s' % content)
        self.log('mode: %s' % mode)
        self.jw_login(username, password, cookies)
        self.do_evaluate(content, mode)

    def jw_login(self, username, password, cookies):
        for cookie in cookies:
            self.session.cookies.set(cookie.name, cookie.value)
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
        if '用户名或密码不正确' in response.text:
            self.log('用户名或密码不正确')
            raise CustomException(Result.failed(msg='用户名或密码不正确'))
        if '请先滑动图片进行验证' in response.text:
            self.log('滑动验证码处理失败')
            raise CustomException(Result.failed(msg='处理失败，请稍后重试'))
        self.log('教务系统登录成功')


if __name__ == '__main__':
    # 处理滑动验证码
    p = CaptchaProcessor()
    dis = p.detect_distance()
    track = p.movement_track_generate(dis)
    status = p.submit(track)
    if status == 'success':
        # 获取验证成功后的cookies，供后续登录使用
        cookies = p.session.cookies

    # 执行登录和自动评价
    evaluator = Evaluator('学号')
    evaluator.start('学号', '密码', '评价内容', 2, cookies)


