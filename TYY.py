"""
cron: 45 7 * * *
const $ = new Env("天翼云");
"""

import os
import time
import re
import json
import base64
import hashlib
import urllib.parse
import hmac
import rsa
import requests
import random
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("TianYiYun")

# 账号密码从环境变量 TYY 获取，格式：用户名;密码
creds = os.getenv("TYY")
assert creds and ";" in creds, "请设置环境变量 TYY，格式为 用户名;密码"
username, password = creds.split(";", 1)

# 钉钉机器人
ddtoken = ""
ddsecret = ""

# Cookie 文件路径
COOKIE_FILE = "cookie.json"

BI_RM = list("0123456789abcdefghijklmnopqrstuvwxyz")
B64MAP = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

def int2char(a):
    return BI_RM[a]

def b64tohex(a):
    d, e, c = "", 0, 0
    for ch in a:
        if ch != "=":
            v = B64MAP.index(ch)
            if e == 0:
                e = 1
                d += int2char(v >> 2)
                c = 3 & v
            elif e == 1:
                e = 2
                d += int2char(c << 2 | v >> 4)
                c = 15 & v
            elif e == 2:
                e = 3
                d += int2char(c)
                d += int2char(v >> 2)
                c = 3 & v
            else:
                e = 0
                d += int2char(c << 2 | v >> 4)
                d += int2char(15 & v)
    if e == 1:
        d += int2char(c << 2)
    return d

def rsa_encode(j_rsakey, string):
    rsa_key = f"-----BEGIN PUBLIC KEY-----\n{j_rsakey}\n-----END PUBLIC KEY-----"
    pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(rsa_key.encode())
    return b64tohex(base64.b64encode(rsa.encrypt(string.encode(), pubkey)).decode())

def save_cookie(session):
    with open(COOKIE_FILE, "w") as f:
        cookies_dict = requests.utils.dict_from_cookiejar(session.cookies)
        json.dump(cookies_dict, f)

def load_cookie():
    if not os.path.exists(COOKIE_FILE):
        return None
    with open(COOKIE_FILE, "r") as f:
        cookies_dict = json.load(f)
    session = requests.Session()
    session.cookies = requests.utils.cookiejar_from_dict(cookies_dict)
    test_url = f"https://api.cloud.189.cn/mkt/userSign.action?rand={int(time.time()*1000)}&clientType=TELEANDROID&version=8.6.3&model=SM-G930K"
    try:
        resp = session.get(test_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        if resp.status_code == 200 and "isSign" in resp.text:
            logger.info("使用本地 cookie 登录成功")
            return session
    except Exception as e:
        logger.warning(f"cookie 检测失败：{e}")
    logger.info("cookie 失效或不存在，准备重新登录")
    return None

def login(username, password):
    s = requests.Session()
    try:
        urlToken = "https://m.cloud.189.cn/udb/udb_login.jsp?pageId=1&pageKey=default&clientType=wap&redirectURL=https://m.cloud.189.cn/zhuanti/2021/shakeLottery/index.html"
        r = s.get(urlToken)
        url = re.search(r"https?://[^\s'\"]+", r.text).group()
        r = s.get(url)
        href = re.search(r'<a id="j-tab-login-link"[^>]*href="([^"]+)"', r.text).group(1)
        r = s.get(href)
        captchaToken = re.findall(r"captchaToken' value='(.+?)'", r.text)[0]
        lt = re.findall(r'lt = "(.+?)"', r.text)[0]
        returnUrl = re.findall(r"returnUrl= '(.+?)'", r.text)[0]
        paramId = re.findall(r'paramId = "(.+?)"', r.text)[0]
        j_rsakey = re.findall(r'j_rsaKey" value="(\S+)"', r.text)[0]

        s.headers.update({"lt": lt})
        u = rsa_encode(j_rsakey, username)
        p = rsa_encode(j_rsakey, password)

        url = "https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do"
        data = {
            "appKey": "cloud",
            "accountType": "01",
            "userName": f"{{RSA}}{u}",
            "password": f"{{RSA}}{p}",
            "validateCode": "",
            "captchaToken": captchaToken,
            "returnUrl": returnUrl,
            "mailSuffix": "@189.cn",
            "paramId": paramId
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://open.e.189.cn/"
        }
        r = s.post(url, data=data, headers=headers, timeout=5)
        if r.json().get("result") != 0:
            logger.error("登录失败：" + r.json().get("msg", "未知错误"))
            return None
        r = s.get(r.json()['toUrl'])
        logger.info("账号密码登录成功")
        return s
    except Exception as e:
        logger.error(f"登录出错：{e}")
        return None

def sign_and_draw(session):
    rand = str(round(time.time() * 1000))
    urls = [
        f'https://api.cloud.189.cn/mkt/userSign.action?rand={rand}&clientType=TELEANDROID&version=8.6.3&model=SM-G930K',
        'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN&activityId=ACT_SIGNIN',
        'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN_PHOTOS&activityId=ACT_SIGNIN',
        'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_2022_FLDFS_KJ&activityId=ACT_SIGNIN'
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 5.1.1; SM-G930K)",
        "Referer": "https://m.cloud.189.cn/zhuanti/2016/sign/index.jsp?albumBackupOpened=1",
        "Host": "m.cloud.189.cn"
    }

    results = []
    for i, url in enumerate(urls):
        time.sleep(random.randint(2, 5))
        r = session.get(url, headers=headers)
        try:
            js = r.json()
        except:
            js = {}
        if i == 0:
            if js.get("isSign") == "false":
                msg = f"未签到，获得{js.get('netdiskBonus')}M"
            else:
                msg = f"已签到，获得{js.get('netdiskBonus')}M"
        elif "prizeName" in js:
            msg = f""
        elif "description" in js:
            msg = f""
        else:
            msg = ""
        logger.info(msg)
        results.append(msg)
    return results

def dingtalk_notify(messages):
    if not ddtoken.strip():
        return
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f'{timestamp}\n{ddsecret}'
    sign = urllib.parse.quote_plus(base64.b64encode(hmac.new(ddsecret.encode(), string_to_sign.encode(), hashlib.sha256).digest()))
    url = f'https://oapi.dingtalk.com/robot/send?access_token={ddtoken}&timestamp={timestamp}&sign={sign}'
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "text",
        "text": {"content": "\n".join(messages)},
        "at": {"isAtAll": False}
    }
    requests.post(url, headers=headers, data=json.dumps(data))
    logger.info("钉钉通知发送成功")

def main():
    session = load_cookie()
    if not session:
        session = login(username, password)
        if not session:
            return
        save_cookie(session)
    results = sign_and_draw(session)
    dingtalk_notify(results)

if __name__ == "__main__":
    main()
