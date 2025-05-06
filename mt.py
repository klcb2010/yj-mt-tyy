"""
//更新时间：2025/5/6
//作者：wdvipa（原作者），夺命梵音（优化）
//支持青龙和actions定时执行
//使用方法：创建变量 名字：mt 内容：账号|密码
//例如: 111|1111
//优化内容：精简日志、防止脚本检测、增强错误处理、移除多账号功能
//推送配置：将需要的推送写入变量mt_fs，多个用&隔开（如 push&tel）
//如使用push推送，需添加mt_push变量，内容为push的token
"""
import requests
import os
import time
import re
import json
import random
from fake_useragent import UserAgent

requests.urllib3.disable_warnings()

# 初始化环境变量和全局变量
ttoken = ""
tuserid = ""
push_token = ""
SKey = ""
QKey = ""
ktkey = ""
msgs = ""

# 检测推送配置和账号信息
if "mt_fs" in os.environ:
    fs = os.environ.get('mt_fs')
    fss = fs.split("&")
    if "tel" in fss and "mt_telkey" in os.environ:
        telekey = os.environ.get("mt_telkey")
        telekeys = telekey.split('\n')
        ttoken = telekeys[0]
        tuserid = telekeys[1]
    if "qm" in fss and "mt_qkey" in os.environ:
        QKey = os.environ.get("mt_qkey")
    if "stb" in fss and "mt_skey" in os.environ:
        SKey = os.environ.get("mt_skey")
    if "push" in fss and "mt_push" in os.environ:
        push_token = os.environ.get("mt_push")
    if "kt" in fss and "mt_ktkey" in os.environ:
        ktkey = os.environ.get("mt_ktkey")

if "mt" in os.environ:
    data = os.environ.get("mt")
    profile = data.split('|')
    if len(profile) != 2:
        print('账号信息格式错误，应为：账号|密码')
        exit()
    username, password = profile
else:
    print('您没有输入任何信息')
    exit()

class MTForumSign(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.ua = UserAgent()
        self.tele_api_url = 'https://api.telegram.org'
        self.tele_bot_token = ttoken
        self.tele_user_id = tuserid

    def sign(self):
        """执行签到流程"""
        headers = {'User-Agent': self.ua.random}
        session = requests.session()
        session.headers = headers

        # 模拟访问首页，增加伪装
        session.get('https://bbs.binmt.cc/', headers=headers)
        time.sleep(random.uniform(3, 8))

        # 获取登录所需的 loginhash 和 formhash
        hash_url = 'https://bbs.binmt.cc/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login'
        try:
            text = session.get(url=hash_url).text
            loginhash = re.findall('loginhash=(.*?)">', text, re.S)[0]
            formhash = re.findall('formhash" value="(.*?)".*? />', text, re.S)[0]
        except IndexError:
            print("风控触发，明天再整吧，小心永久黑")
            return "签到失败：页面结构异常"

        headers['referer'] = hash_url
        time.sleep(random.uniform(3, 8))

        # 模拟登录
        login_url = f'https://bbs.binmt.cc/member.php?mod=logging&action=login&loginsubmit=yes&handlekey=login&loginhash={loginhash}&inajax=1'
        data = {
            'formhash': formhash,
            'referer': 'https://bbs.binmt.cc/index.php',
            'loginfield': 'username',
            'username': self.username,
            'password': self.password,
            'questionid': '0',
            'answer': '',
        }
        text = session.post(url=login_url, data=data).text
        if 'root' not in text:
            print("登录失败")
            return "登录失败"

        print("登录成功")
        time.sleep(random.uniform(3, 8))

        # 获取签到页面，检查是否已签到
        sign_page_url = 'https://bbs.binmt.cc/k_misign-sign.html'
        sign_page = session.get(url=sign_page_url).text
        if '今日已签' in sign_page:
            print("今日已签到，跳过签到")
            return self._extract_sign_info(sign_page)

        # 获取签到所需的 formhash
        try:
            formhash = re.findall('formhash" value="(.*?)".*? />', sign_page, re.S)[0]
        except IndexError:
            print("无法提取签到 formhash，页面结构可能已变更")
            return "签到失败：页面结构异常"

        # 模拟签到
        sign_url = f'https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&format=text&formhash={formhash}'
        sign_result = session.get(url=sign_url).text
        if '<root><' not in sign_result:
            print("签到失败")
            return "签到失败"

        # 提取签到信息
        sign_page = session.get(url=sign_page_url).text
        return self._extract_sign_info(sign_page)

    def _extract_sign_info(self, page_content):
        """提取签到信息并格式化为精简日志"""
        try:
            name = re.findall('<div id="comiis_key".*?<span>(.*?)</span>.*?</div>', page_content, re.S)[0]
            pm = re.findall('签到排名：(.*?)</div>', page_content, re.S)[0]
            lxb = re.findall('连续签到</h4>.*?</span>', page_content, re.S)
            djb = re.findall('签到等级</h4>.*?</span>', page_content, re.S)
            jib = re.findall('积分奖励</h4>.*?</span>', page_content, re.S)
            ztsb = re.findall('签到等级</h4>.*?</span>', page_content, re.S)

            lx = re.findall('value="(.*?)"', str(lxb))[0]
            dj = re.findall('value="(.*?)"', str(djb))[0]
            jb = re.findall('value="(.*?)"', str(jib))[0]
            zts = re.findall('value="(.*?)"', str(ztsb))[0]

            message = f"""：
账号昵称：{name}
签到排名：{pm}
连续签到：{lx}天
签到等级：LV.{dj}
获得金币：{jb}
总天数：{zts}天"""
            print(message)
            return message
        except Exception as e:
            print(f"提取签到信息失败：{str(e)}")
            return "签到失败：提取信息错误"

    def tele_send(self, msg):
        """Telegram 推送"""
        if self.tele_bot_token == '':
            return
        tele_url = f"{self.tele_api_url}/bot{self.tele_bot_token}/sendMessage"
        data = {
            'chat_id': self.tele_user_id,
            'parse_mode': "Markdown",
            'text': msg
        }
        requests.post(tele_url, data=data)

    def pushplus_send(self, msg):
        """Pushplus 推送"""
        if push_token == '':
            return
        url = 'http://www.pushplus.plus/send'
        data = {
            "token": push_token,
            "title": "MT论坛签到通知",
            "content": msg
        }
        headers = {'Content-Type': 'application/json'}
        requests.post(url, data=json.dumps(data), headers=headers)

    def main(self):
        """主流程"""
        global msgs
        result = self.sign()
        msgs = result
        return result

if __name__ == '__main__':
    start_time = time.time()

    sign_task = MTForumSign(username, password)
    sign_task.main()
    if msgs:
        sign_task.pushplus_send(msgs)
        sign_task.tele_send(msgs)
    end_time = time.time()
