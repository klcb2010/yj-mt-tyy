'''
cron: 0 45 7 * * *
const $ = new Env("天翼云");
'''

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

# 加载环境变量
creds = os.getenv("TYY")
assert creds and ";" in creds, "请设置环境变量 TYY，格式为 用户名;密码，例如：1454545452;44kkl4545545"
username, password = creds.split(";", 1)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("TianYiYun")

BI_RM = list("0123456789abcdefghijklmnopqrstuvwxyz")
B64MAP = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

s = requests.Session()

# 钉钉机器人token
ddtoken = ""
ddsecret = ""

def int2char(a):
    return BI_RM[a]

def b64tohex(a):
    d = ""
    e = 0
    c = 0
    for i in range(len(a)):
        if list(a)[i] != "=":
            v = B64MAP.index(list(a)[i])
            if 0 == e:
                e = 1
                d += int2char(v >> 2)
                c = 3 & v
            elif 1 == e:
                e = 2
                d += int2char(c << 2 | v >> 4)
                c = 15 & v
            elif 2 == e:
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
    result = b64tohex((base64.b64encode(rsa.encrypt(f'{string}'.encode(), pubkey))).decode())
    return result

def calculate_md5_sign(params):
    return hashlib.md5('&'.join(sorted(params.split('&'))).encode('utf-8')).hexdigest()

def login(username, password):
    url = ""
    urlToken = "https://m.cloud.189.cn/udb/udb_login.jsp?pageId=1&pageKey=default&clientType=wap&redirectURL=https://m.cloud.189.cn/zhuanti/2021/shakeLottery/index.html"
    s = requests.Session()
    r = s.get(urlToken)
    pattern = r"https?://[^\s'\"]+"
    match = re.search(pattern, r.text)
    if match:
        url = match.group()
    else:
        logger.error("没有找到url")

    r = s.get(url)
    pattern = r"<a id=\"j-tab-login-link\"[^>]*href=\"([^\"]+)\""
    match = re.search(pattern, r.text)
    if match:
        href = match.group(1)
    else:
        logger.error("没有找到href链接")

    r = s.get(href)
    captchaToken = re.findall(r"captchaToken' value='(.+?)'", r.text)[0]
    lt = re.findall(r'lt = "(.+?)"', r.text)[0]
    returnUrl = re.findall(r"returnUrl= '(.+?)'", r.text)[0]
    paramId = re.findall(r'paramId = "(.+?)"', r.text)[0]
    j_rsakey = re.findall(r'j_rsaKey" value="(\S+)"', r.text, re.M)[0]
    s.headers.update({"lt": lt})

    username = rsa_encode(j_rsakey, username)
    password = rsa_encode(j_rsakey, password)
    url = "https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/76.0',
        'Referer': 'https://open.e.189.cn/',
    }
    data = {
        "appKey": "cloud",
        "accountType": '01',
        "userName": f"{{RSA}}{username}",
        "password": f"{{RSA}}{password}",
        "validateCode": "",
        "captchaToken": captchaToken,
        "returnUrl": returnUrl,
        "mailSuffix": "@189.cn",
        "paramId": paramId
    }
    r = s.post(url, data=data, headers=headers, timeout=5)
    if r.json()['result'] == 0:
        logger.info(r.json()['msg'])
    else:
        logger.error(r.json()['msg'])
    redirect_url = r.json()['toUrl']
    r = s.get(redirect_url)
    return s

def main():
    s = login(username, password)
    rand = str(round(time.time() * 1000))
    surl = f'https://api.cloud.189.cn/mkt/userSign.action?rand={rand}&clientType=TELEANDROID&version=8.6.3&model=SM-G930K'
    url = f'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN&activityId=ACT_SIGNIN'
    url2 = f'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN_PHOTOS&activityId=ACT_SIGNIN'
    url3 = f'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_2022_FLDFS_KJ&activityId=ACT_SIGNIN'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 5.1.1; SM-G930K Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36 Ecloud/8.6.3 Android/22 clientId/355325117317828 clientModel/SM-G930K imsi/460071114317824 clientChannelId/qq proVersion/1.0.6',
        "Referer": "https://m.cloud.189.cn/zhuanti/2016/sign/index.jsp?albumBackupOpened=1",
        "Host": "m.cloud.189.cn",
        "Accept-Encoding": "gzip, deflate",
    }

    response = s.get(surl, headers=headers)
    netdiskBonus = response.json()['netdiskBonus']
    if response.json()['isSign'] == "false":
        logger.info(f"未签到，签到获得{netdiskBonus}M空间")
        res1 = f"未签到，签到获得{netdiskBonus}M空间"
    else:
        logger.info(f"签到获得{netdiskBonus}M空间")
        res1 = f"已经签到过了，签到获得{netdiskBonus}M空间"

    # URL 1
    response = s.get(url, headers=headers)
    if "errorCode" in response.text:
        if "User_Not_Chance" in response.text:
            res2 = ""
        else:
            logger.error(response.text)
            res2 = ""
    else:
        description = response.json()['description']
        if description != '1':
            logger.info(f"抽奖获得{description}")
            res2 = f"抽奖获得{description}"
        else:
            res2 = ""

    time.sleep(random.randint(5, 10))

    # URL 2
    response = s.get(url2, headers=headers)
    if "errorCode" in response.text:
        if "User_Not_Chance" in response.text:
            res3 = ""
        else:
            logger.error(response.text)
            res3 = ""
    else:
        description = response.json()['prizeName']
        logger.info(f"抽奖获得{description}")
        res3 = f"抽奖获得{description}"

    time.sleep(random.randint(5, 10))

    # URL 3
    response = s.get(url3, headers=headers)
    if "errorCode" in response.text:
        if "User_Not_Chance" in response.text:
            res4 = ""
        else:
            logger.error(response.text)
            res4 = ""
    else:
        description = response.json()['prizeName']
        logger.info(f"链接3抽奖获得{description}")
        res4 = f"链接3抽奖获得{description}"

    # 钉钉通知
    if ddtoken.strip():
        _ = ddtoken.strip()
        timestamp = str(round(time.time() * 1000))
        secret_enc = ddsecret.encode('utf-8')
        string_to_sign = f"{timestamp}\n{ddsecret}"
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        url = f'https://oapi.dingtalk.com/robot/send?access_token={ddtoken}&timestamp={timestamp}&sign={sign}'
        headers = {
            "Content-Type": "application/json",
            "Charset": "UTF-8"
        }
        data = {
            "msgtype": "text",
            "text": {
                "content": f"{res1}\n{res2}\n{res3}\n{res4}"
            },
            "at": {
                "atMobiles": [""],
                "isAtAll": False
            }
        }
        sendData = json.dumps(data)
        requests.post(url, headers=headers, data=sendData)
        logger.info("钉钉消息发送成功")

if __name__ == "__main__":
    main()
