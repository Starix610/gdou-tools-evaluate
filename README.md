## 一键评价Python脚本
### 介绍
一个Python实现的gdou教务系统教学自动评价脚本，除了能在本地直接运行使用外，也包含一个简单的后端服务，提供HTTP接口能力。

### 本地部署使用

#### 1. 环境版本
Python 3.6.5及以上

#### 2. 安装依赖库
+ requests
+ BeautifulSoup4
+ base64
+ rsa
+ fastapi
+ uvicorn
#### 3. 修改代码配置
第一步：修改evaluate.py文件中的开头内容：
```python
webvpn_username = 'xxxxxxxxxxxx'
webvpn_password = 'xxxx'
```
修改此处webvpn登录的账号密码（网上办事大厅的账号密码）为你自己的，目前登录教务系统需要先经过webvpn，所以这个必填。经测试发现：一个webvpn账号登录后可以给不同的教务系统账号进行登录，因此这个只需填写一个账号就好，即使登录其它的教务系统账号也无需更改。

第二步：
修改evaluate.py文件main函数入口处调用的参数：
```python
if __name__ == '__main__':
    evaluator = Evaluator()
    evaluator.start('username', 'password', 'content', 1)
```
修改此处调用start方法传递的四个参数，username和passowrd是教务系统的账号和密码，content是评价的内容，最后一个参数是评价的提交模式：0代表手动提交，1代表自动提交，两个模式的含义可以看我公众号推文中的具体解释。