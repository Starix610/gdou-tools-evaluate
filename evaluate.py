import base64
from datetime import datetime
import random
from urllib import parse
from bs4 import BeautifulSoup
import requests
import rsa
from email_util import send_email
from result import CustomException
from result import Result

webvpn_username = 'xxxxxxxxxxxx'
webvpn_password = 'xxxxxxxxxxxx'


class Evaluator:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/79.0.3945.130 Safari/537.36'
    }
    base_url = 'https://webvpn.gdou.edu.cn'
    # 这是教务系统第二个地址，后期可以根据需要做成可选的
    base_url_jw = base_url + '/http/77726476706e69737468656265737421a2a611d2746826012d5fc7f4cc'

    def __init__(self, username):
        # 全局同一会话状态request对象
        self.session = requests.session()
        self.current_user = username

    def webvpn_login(self):
        webvpn_login_url = self.base_url + "/do-login?local_login=true"
        data = {
            'auth_type': 'local',
            'username': webvpn_username,
            'sms_code': '',
            'password': webvpn_password,
            'needCaptcha': 'false',
        }
        response = self.session.post(url=webvpn_login_url, data=data, headers=self.headers)
        if response.json()['success']:
            self.log('webvpn登录成功: %s' % self.session.cookies['wengine_vpn_ticketwebvpn_gdou_edu_cn'])
        elif response.json()['error'] == 'NEED_CONFIRM':
            # 存在已登录的客户端，点确认踢掉
            self.webvpn_confirm_login()
        else:
            self.log('webvpn登录失败: %s' % response.json())
            send_email('646722505@qq.com', '内置webvpn登录失败', '内置webvpn登录失败，详情：%s' % response.json())
            raise CustomException(Result.failed(msg='内置WEBVPN异常，等待修复'))

    def webvpn_confirm_login(self):
        self.log('踢掉已登录的webvpn客户端: %s' % self.session.cookies['wengine_vpn_ticketwebvpn_gdou_edu_cn'])
        webvpn_confirm_login_url = self.base_url + '/do-confirm-login'
        response = self.session.post(webvpn_confirm_login_url, headers=self.headers)
        if response.json()['success']:
            self.log('webvpn登录成功: %s' % self.session.cookies['wengine_vpn_ticketwebvpn_gdou_edu_cn'])
        else:
            self.log('webvpn登录失败: %s' % response.json())
            send_email('646722505@qq.com', '内置webvpn登录失败', '内置webvpn登录失败，详情：%s' % response.json())
            raise CustomException(Result.failed(msg='内置WEBVPN异常，等待修复'))

    def webvpn_logout(self):
        webvpn_logout_url = self.base_url + '/logout'
        self.session.get(webvpn_logout_url, headers=self.headers)
        self.log('webvpn注销成功: %s' % self.session.cookies['wengine_vpn_ticketwebvpn_gdou_edu_cn'])

    def jw_login(self, username, password):
        # 获取密码加密公钥需要的参数
        publickey_url = self.base_url_jw + '/xtgl/login_getPublicKey.html'
        publickey = self.session.get(publickey_url, headers=self.headers).json()
        # 将base64解码转为bytes
        b_modulus = base64.b64decode(publickey['modulus'])
        b_exponent = base64.b64decode(publickey['exponent'])
        # 公钥生成,python3从bytes中获取int:int.from_bytes(bstring,'big')
        rsa_key = rsa.PublicKey(int.from_bytes(b_modulus, 'big'), int.from_bytes(b_exponent, 'big'))
        # 利用公钥加密,bytes转为base64编码
        encrypt_password = base64.b64encode(rsa.encrypt(password.encode(), rsa_key)).decode()
        jw_login_url = self.base_url_jw + '/xtgl/login_slogin.html'
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
            'yhm': username,
            'mm': encrypt_password
        }
        response = self.session.post(jw_login_url, data=data, headers=self.headers)
        if '用户名或密码不正确' in response.text:
            self.log('用户名或密码不正确')
            raise CustomException(Result.failed(msg='用户名或密码不正确'))
        self.log('教务系统登录成功')

    def get_course_list(self):
        url = self.base_url_jw + '/xspjgl/xspj_cxXspjIndex.html?doType=query&gnmkdm=N401605'
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
        self.log('共%s门课程' % total_count)
        course_list = []
        for page in range(total_page):
            data['queryModel.currentPage'] = page + 1
            json = self.session.post(url, data=data, headers=self.headers).json()
            course_items = json['items']
            for item in course_items:
                # 筛选未提交的评价
                if item['tjzt'] != "1":
                    course_list.append(item)
        if not course_list:
            self.log('已完成所有评价，无需再次评价')
            raise CustomException(Result.failed(msg='你已经完成所有评价啦，无需再次评价，请到官网查看！'))
        return course_list

    def do_evaluate(self, content, mode):
        save_evaluation_url = self.base_url_jw + '/xspjgl/xspj_bcXspj.html?gnmkdm=N401605'
        course_list = self.get_course_list()
        self.log('开始自动评价...')
        for i, course in enumerate(course_list):
            self.log('--->%s-%s' % (course['kcmc'], course['xsmc']))
            # 先进入评价详情页获取相关参数，主要是xspfb_id这个参数。当前已评价的情况下需要有这个参数才能正常进行评价内容更新。
            evaluation_detail_url = self.base_url_jw + '/xspjgl/xspj_cxXspjDisplay.html?gnmkdm=N401605'
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
            soup = BeautifulSoup(response.text, "html.parser")
            pj_panel_body = soup.find(attrs={'class': 'panel-body xspj-body'})
            sub_divs = pj_panel_body.find_all(attrs={'class': 'panel panel-default panel-pjdx'})
            # 评价教师参数
            data = {
                'ztpjbl': pj_panel_body['data-ztpjbl'],
                'jszdpjbl': pj_panel_body['data-jszdpjbl'],
                'xykzpjbl': pj_panel_body['data-xykzpjbl'],
                'jxb_id': course['jxb_id'],
                'kch_id': course['kch_id'],
                'jgh_id': course['jgh_id'],
                'xsdm': course['xsdm'],
                # 评价提交状态参数，取值含义：已评价并保存过当前课程：0，已提交评价：1，未评价：-1
                'tjzt': course['tjzt'],
                # ====================================评价教师参数区 start====================================
                'modelList[0].pjmbmcb_id': sub_divs[0]['data-pjmbmcb_id'],
                'modelList[0].pjdxdm': sub_divs[0]['data-pjdxdm'],
                'modelList[0].py': parse.quote(content),
                'modelList[0].xspfb_id': sub_divs[0]['data-xspfb_id'],
                # 评价状态参数，取值含义：已评价并保存（已评完）：1，未评完/未评价：0。
                # 所以如果需要在评价完成后将当前课程评价状态设置为已评完，则需要将该值设置为1，设置为0则会显示为未评完状态
                'modelList[0].pjzt': 1,
                # 【教学基本情况评价选项】
                'modelList[0].xspjList[0].childXspjList[0].pfdjdmxmb_id': 'A44133C16D2333CAE053C7EBFF74E4B8',
                'modelList[0].xspjList[0].childXspjList[1].pfdjdmxmb_id': 'A44133C16D2333CAE053C7EBFF74E4B8',
                'modelList[0].xspjList[0].childXspjList[2].pfdjdmxmb_id': 'A44133C16D2333CAE053C7EBFF74E4B8',
                'modelList[0].xspjList[0].childXspjList[3].pfdjdmxmb_id': 'A44133C16D2333CAE053C7EBFF74E4B8',
                'modelList[0].xspjList[0].childXspjList[4].pfdjdmxmb_id': 'A44133C16D2333CAE053C7EBFF74E4B8',
                'modelList[0].xspjList[0].childXspjList[5].pfdjdmxmb_id': 'A44133C16D2333CAE053C7EBFF74E4B8',
                'modelList[0].xspjList[0].childXspjList[6].pfdjdmxmb_id': 'A44133C16D2333CAE053C7EBFF74E4B8',
                # 【参数1】（每一条都不一样）
                'modelList[0].xspjList[0].pjzbxm_id': 'A7CB5925C3D7527FE053C7EBFF747BE5',
                'modelList[0].xspjList[0].childXspjList[0].pjzbxm_id': 'A7CB5925C3D9527FE053C7EBFF747BE5',
                'modelList[0].xspjList[0].childXspjList[1].pjzbxm_id': 'A7CB5925C3DA527FE053C7EBFF747BE5',
                'modelList[0].xspjList[0].childXspjList[2].pjzbxm_id': 'A7CB5925C3DB527FE053C7EBFF747BE5',
                'modelList[0].xspjList[0].childXspjList[3].pjzbxm_id': 'A7CB5925C3DC527FE053C7EBFF747BE5',
                'modelList[0].xspjList[0].childXspjList[4].pjzbxm_id': 'A7CB5925C3DD527FE053C7EBFF747BE5',
                'modelList[0].xspjList[0].childXspjList[5].pjzbxm_id': 'A7CB5925C3DE527FE053C7EBFF747BE5',
                'modelList[0].xspjList[0].childXspjList[6].pjzbxm_id': 'A7CB5925C3DF527FE053C7EBFF747BE5',
                # 【参数2】（两个模块一样）
                'modelList[0].xspjList[0].childXspjList[0].pfdjdmb_id': 'A44133C16D2133CAE053C7EBFF74E4B8',
                'modelList[0].xspjList[0].childXspjList[1].pfdjdmb_id': 'A44133C16D2133CAE053C7EBFF74E4B8',
                'modelList[0].xspjList[0].childXspjList[2].pfdjdmb_id': 'A44133C16D2133CAE053C7EBFF74E4B8',
                'modelList[0].xspjList[0].childXspjList[3].pfdjdmb_id': 'A44133C16D2133CAE053C7EBFF74E4B8',
                'modelList[0].xspjList[0].childXspjList[4].pfdjdmb_id': 'A44133C16D2133CAE053C7EBFF74E4B8',
                'modelList[0].xspjList[0].childXspjList[5].pfdjdmb_id': 'A44133C16D2133CAE053C7EBFF74E4B8',
                'modelList[0].xspjList[0].childXspjList[6].pfdjdmb_id': 'A44133C16D2133CAE053C7EBFF74E4B8',
                # 【参数3】（两个模块不一样）
                'modelList[0].xspjList[0].childXspjList[0].zsmbmcb_id': 'A7CB5925C3D6527FE053C7EBFF747BE5',
                'modelList[0].xspjList[0].childXspjList[1].zsmbmcb_id': 'A7CB5925C3D6527FE053C7EBFF747BE5',
                'modelList[0].xspjList[0].childXspjList[2].zsmbmcb_id': 'A7CB5925C3D6527FE053C7EBFF747BE5',
                'modelList[0].xspjList[0].childXspjList[3].zsmbmcb_id': 'A7CB5925C3D6527FE053C7EBFF747BE5',
                'modelList[0].xspjList[0].childXspjList[4].zsmbmcb_id': 'A7CB5925C3D6527FE053C7EBFF747BE5',
                'modelList[0].xspjList[0].childXspjList[5].zsmbmcb_id': 'A7CB5925C3D6527FE053C7EBFF747BE5',
                'modelList[0].xspjList[0].childXspjList[6].zsmbmcb_id': 'A7CB5925C3D6527FE053C7EBFF747BE5',

                # 【综合指标评价选项】
                'modelList[0].xspjList[1].childXspjList[0].pfdjdmxmb_id': 'A44133C16D2333CAE053C7EBFF74E4B8',
                'modelList[0].xspjList[1].childXspjList[1].pfdjdmxmb_id': 'A44133C16D2333CAE053C7EBFF74E4B8',
                'modelList[0].xspjList[1].childXspjList[2].pfdjdmxmb_id': 'A44133C16D2333CAE053C7EBFF74E4B8',
                # 【参数1】
                'modelList[0].xspjList[1].pjzbxm_id': 'A7CB5925C3D8527FE053C7EBFF747BE5',
                'modelList[0].xspjList[1].childXspjList[0].pjzbxm_id': 'A7CB5925C3E0527FE053C7EBFF747BE5',
                'modelList[0].xspjList[1].childXspjList[1].pjzbxm_id': 'A7CB5925C3E1527FE053C7EBFF747BE5',
                'modelList[0].xspjList[1].childXspjList[2].pjzbxm_id': 'A7CB5925C3E2527FE053C7EBFF747BE5',
                # 【参数2】
                'modelList[0].xspjList[1].childXspjList[0].pfdjdmb_id': 'A44133C16D2133CAE053C7EBFF74E4B8',
                'modelList[0].xspjList[1].childXspjList[1].pfdjdmb_id': 'A44133C16D2133CAE053C7EBFF74E4B8',
                'modelList[0].xspjList[1].childXspjList[2].pfdjdmb_id': 'A44133C16D2133CAE053C7EBFF74E4B8',
                # 【参数3】
                'modelList[0].xspjList[1].childXspjList[0].zsmbmcb_id': 'A7CB5925C3D6527FE053C7EBFF747BE5',
                'modelList[0].xspjList[1].childXspjList[1].zsmbmcb_id': 'A7CB5925C3D6527FE053C7EBFF747BE5',
                'modelList[0].xspjList[1].childXspjList[2].zsmbmcb_id': 'A7CB5925C3D6527FE053C7EBFF747BE5',
                # =====================================评价教师参数区 end=====================================
            }

            # 当前课程需要同时评价教师和教材
            if len(sub_divs) >= 2:
                # 评价教材参数
                textbook_data = {
                    # ====================================评价教材参数区 start====================================
                    'modelList[1].pjmbmcb_id': sub_divs[1]['data-pjmbmcb_id'],
                    'modelList[1].pjdxdm': sub_divs[1]['data-pjdxdm'],
                    'modelList[1].py': parse.quote(content),
                    'modelList[1].xspfb_id': sub_divs[1]['data-xspfb_id'],
                    'modelList[1].pjzt': 1,
                    # 【教材选用选项】
                    'modelList[1].xspjList[0].childXspjList[0].pfdjdmxmb_id': 'A44133C16D2333CAE053C7EBFF74E4B8',
                    'modelList[1].xspjList[0].childXspjList[1].pfdjdmxmb_id': 'A44133C16D2333CAE053C7EBFF74E4B8',
                    'modelList[1].xspjList[0].childXspjList[2].pfdjdmxmb_id': 'A44133C16D2333CAE053C7EBFF74E4B8',
                    'modelList[1].xspjList[0].childXspjList[3].pfdjdmxmb_id': 'A44133C16D2333CAE053C7EBFF74E4B8',
                    'modelList[1].xspjList[0].childXspjList[4].pfdjdmxmb_id': 'A44133C16D2333CAE053C7EBFF74E4B8',
                    'modelList[1].xspjList[0].childXspjList[5].pfdjdmxmb_id': 'A44133C16D2333CAE053C7EBFF74E4B8',
                    'modelList[1].xspjList[0].childXspjList[6].pfdjdmxmb_id': 'A44133C16D2333CAE053C7EBFF74E4B8',
                    'modelList[1].xspjList[0].childXspjList[7].pfdjdmxmb_id': 'A44133C16D2333CAE053C7EBFF74E4B8',
                    'modelList[1].xspjList[0].childXspjList[8].pfdjdmxmb_id': 'A44133C16D2333CAE053C7EBFF74E4B8',
                    # 【参数1】
                    'modelList[1].xspjList[0].pjzbxm_id': 'A7EE842C7510B886E053C7EBFF74A0CF',
                    'modelList[1].xspjList[0].childXspjList[0].pjzbxm_id': 'A7EE842C7511B886E053C7EBFF74A0CF',
                    'modelList[1].xspjList[0].childXspjList[1].pjzbxm_id': 'A7EE842C7512B886E053C7EBFF74A0CF',
                    'modelList[1].xspjList[0].childXspjList[2].pjzbxm_id': 'A7EE842C7513B886E053C7EBFF74A0CF',
                    'modelList[1].xspjList[0].childXspjList[3].pjzbxm_id': 'A7EE842C7514B886E053C7EBFF74A0CF',
                    'modelList[1].xspjList[0].childXspjList[4].pjzbxm_id': 'A7EE842C7515B886E053C7EBFF74A0CF',
                    'modelList[1].xspjList[0].childXspjList[5].pjzbxm_id': 'A7EE842C7516B886E053C7EBFF74A0CF',
                    'modelList[1].xspjList[0].childXspjList[6].pjzbxm_id': 'A7EE842C7517B886E053C7EBFF74A0CF',
                    'modelList[1].xspjList[0].childXspjList[7].pjzbxm_id': 'A7EE842C7518B886E053C7EBFF74A0CF',
                    'modelList[1].xspjList[0].childXspjList[8].pjzbxm_id': 'A7EE842C7519B886E053C7EBFF74A0CF',
                    # 【参数2】
                    'modelList[1].xspjList[0].childXspjList[0].pfdjdmb_id': 'A44133C16D2133CAE053C7EBFF74E4B8',
                    'modelList[1].xspjList[0].childXspjList[1].pfdjdmb_id': 'A44133C16D2133CAE053C7EBFF74E4B8',
                    'modelList[1].xspjList[0].childXspjList[2].pfdjdmb_id': 'A44133C16D2133CAE053C7EBFF74E4B8',
                    'modelList[1].xspjList[0].childXspjList[3].pfdjdmb_id': 'A44133C16D2133CAE053C7EBFF74E4B8',
                    'modelList[1].xspjList[0].childXspjList[4].pfdjdmb_id': 'A44133C16D2133CAE053C7EBFF74E4B8',
                    'modelList[1].xspjList[0].childXspjList[5].pfdjdmb_id': 'A44133C16D2133CAE053C7EBFF74E4B8',
                    'modelList[1].xspjList[0].childXspjList[6].pfdjdmb_id': 'A44133C16D2133CAE053C7EBFF74E4B8',
                    'modelList[1].xspjList[0].childXspjList[7].pfdjdmb_id': 'A44133C16D2133CAE053C7EBFF74E4B8',
                    'modelList[1].xspjList[0].childXspjList[8].pfdjdmb_id': 'A44133C16D2133CAE053C7EBFF74E4B8',
                    # 【参数3】
                    'modelList[1].xspjList[0].childXspjList[0].zsmbmcb_id': 'A7EE842C750FB886E053C7EBFF74A0CF',
                    'modelList[1].xspjList[0].childXspjList[1].zsmbmcb_id': 'A7EE842C750FB886E053C7EBFF74A0CF',
                    'modelList[1].xspjList[0].childXspjList[2].zsmbmcb_id': 'A7EE842C750FB886E053C7EBFF74A0CF',
                    'modelList[1].xspjList[0].childXspjList[3].zsmbmcb_id': 'A7EE842C750FB886E053C7EBFF74A0CF',
                    'modelList[1].xspjList[0].childXspjList[4].zsmbmcb_id': 'A7EE842C750FB886E053C7EBFF74A0CF',
                    'modelList[1].xspjList[0].childXspjList[5].zsmbmcb_id': 'A7EE842C750FB886E053C7EBFF74A0CF',
                    'modelList[1].xspjList[0].childXspjList[6].zsmbmcb_id': 'A7EE842C750FB886E053C7EBFF74A0CF',
                    'modelList[1].xspjList[0].childXspjList[7].zsmbmcb_id': 'A7EE842C750FB886E053C7EBFF74A0CF',
                    'modelList[1].xspjList[0].childXspjList[8].zsmbmcb_id': 'A7EE842C750FB886E053C7EBFF74A0CF',
                    # =====================================评价教材参数区 end=====================================
                }
                # 合并评价教师和评价教材的两个参数字典
                data.update(textbook_data)
                # 随机选取评价教材区域的一个评价项，评价为“较好”
                random_index = random.randint(0, 8)
                data[
                    'modelList[1].xspjList[0].childXspjList[%s].pfdjdmxmb_id' % random_index] = 'A44133C16D2433CAE053C7EBFF74E4B8'
            else:
                # 如果当前课程无教材评价则随机选取评价教师区域的一个评价项，评价为“较好”
                random_index = random.randint(0, 6)
                data[
                    'modelList[0].xspjList[0].childXspjList[%s].pfdjdmxmb_id' % random_index] = 'A44133C16D2433CAE053C7EBFF74E4B8'
            response = self.session.post(save_evaluation_url, data=data, headers=self.headers)
            if '评价保存成功' in response.text:
                self.log('评价保存成功')
            else:
                self.log('评价保存失败: %s' % eval(response.text))
            # 提交所有评价
            if i + 1 == len(course_list) and mode == 1:
                self.submit_evaluation(data)

    def submit_evaluation(self, data):
        submit_evaluation_url = self.base_url_jw + '/xspjgl/xspj_tjXspj.html?gnmkdm=N401605'
        response = self.session.post(submit_evaluation_url, data=data, headers=self.headers)
        if '整体提交成功' in response.text:
            self.log('所有评价已提交成功！')
        else:
            self.log('评价提交失败: %s' % response.text)
            send_email('646722505@qq.com', '评价提交失败', '[%s]评价提交失败，详情：%s' % (self.current_user, response.text))
            raise CustomException(Result.failed(msg='评价提交失败，请稍后重试！'))

    def log(self, info):
        print('[%s] [%s] %s' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.current_user, info))

    def start(self, username, password, content, mode):
        self.log('content: %s, mode: %s' % (content, mode))
        self.webvpn_login()
        self.jw_login(username, password)
        self.do_evaluate(content, mode)
        self.webvpn_logout()


if __name__ == '__main__':
    evaluator = Evaluator('username')
    evaluator.start('username', 'password', 'content', 1)
