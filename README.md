## 自动评价Python脚本
### 介绍
一个Python实现的gdou教务系统教学自动评价脚本，除了能在本地直接运行使用外，也包含一个简单的后端服务，提供HTTP接口能力。
### 目录说明
+ **evaluate.py - 自动评价主要代码**，如果只需要在本地使用，则只需关注这个代码文件
+ evaluate_params.py - 评价参数处理
+ slide_captcha_pass.py - 滑动验证码处理
+ api.py - 提供自动评价HTTP接口
+ result.py - 接口调用统一格式返回结果封装
+ result_status_em.py - 接口调用返回状态码枚举定义
+ wxpush.py - 微信推送工具，这里主要用于线上发生未知异常时推送错误日志，便于及时排查bug


### 本地部署使用
#### 1. 环境版本
Python 3.6.5及以上

#### 2. 安装依赖库
+ requests
+ BeautifulSoup4
+ base64
+ opencv-python
+ numpy
+ PyExecJS
+ rsa
+ fastapi
+ uvicorn
+ wxpusher

#### 3. 修改代码配置

修改evaluate.py文件main入口函数中调用**start**函数的参数，主要修改前四个参数，参数说明：

username：教务系统账号，password：密码，content：评价内容，mode：评价提交模式（1代表自动提交，2代表手动提交），cookies：验证码认证成功后的cookies（自动获取，无需更改）
```python
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
```

#### 4. 运行
在IDE或者命令行下运行evaluate.py，运行后就可以实现给指定的账号进行自动评价。

### 后端接口的部署使用
该脚本目前使用fastapi框架开发了一个简单的python后台服务，提供后端接口来供外部客户端应用来调用自动评价。如果你有需要的话可以部署后端接口来使用。
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