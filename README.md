## 一键评价Python脚本
### 介绍
一个Python实现的gdou教务系统教学自动评价脚本，除了能在本地直接运行使用外，也包含一个简单的后端服务，提供HTTP接口能力。
### 目录说明
+ **evaluate.py - 自动评价主要代码**，如果只需要在本地使用，则只关注这个代码文件
+ api.py - 提供自动评价HTTP接口
+ result.py - 接口调用统一格式返回结果封装
+ result_status_em.py - 接口调用返回状态码枚举定义
+ email_util.py - 发送邮件工具，这里主要用于线上发生未知异常时发送邮件通知，便于及时排查bug


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
+ 第一步：修改evaluate.py文件中开头处的内容
    
    修改此处webvpn登录的账号密码（网上办事大厅的账号密码）为你自己的，目前登录教务系统需要先经过webvpn，所以这个必填。经测试发现：一个webvpn账号登录后可以给不同的教务系统账号进行登录，因此这个只需填写一个账号就好，即使登录其它的教务系统账号也无需更改。
    ```python
    webvpn_username = 'xxxxxxxxxxxx'
    webvpn_password = 'xxxxxxxxxxxx'
    
    ```

+ 第二步：修改evaluate.py文件main函数入口处调用的参数

    修改此处调用start方法传递的四个参数，username和passowrd是教务系统的账号和密码，content是评价的内容，最后一个参数是评价的提交模式：0代表手动提交，1代表自动提交，两个模式的含义可以看公众号推文中的具体解释。初始化Evaluator('username')时传递的username参数也需要修改为你的学号。
    ```python
    if __name__ == '__main__':
        evaluator = Evaluator('username')
        evaluator.start('username', 'password', 'content', 1)
    ```

#### 4. 运行
在IDE或者命令行下运行evaluate.py，运行后就可以实现给指定的账号进行自动评价。

### 后端接口的部署使用
该脚本目前也使用fastapi框架开发了一个简单的python后台服务，提供后端接口来供外部客户端应用来调用自动评价。如果你有需要的话可以部署后端接口来使用。
有两种方式启动后端服务：

方式一：直接运行api.py文件
```shell
python api.py
```
方式二：执行这条命令
```shell
uvicorn api:app --reload
```
启动后可以看到日志输出有如下语句，说明启动成功，需要注意启动的端口号。
```shell
Uvicorn running on http://127.0.0.1:8000
```
然后就可以调用HTTP接口来进行自动评价了，也可以部署到你自己的服务器上并集成到你的应用中。具体接口说明请看：<a href="http://www.starix.top/temp/file/evaluate.pdf" target="_blank">自动评价接口说明</a>