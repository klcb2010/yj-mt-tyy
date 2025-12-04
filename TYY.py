import os
import re
import json
import time
import base64
import hashlib
import rsa
import requests
import logging

# 环境变量：用户名;密码
creds = os.getenv("TYY")
assert creds and ";" in creds, "请设置环境变量 TYY，如： 18612345678;abcdef"
username, password = creds.split(";", 1)

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("TianYiApp")

SESSION_FILE = "/ql/data/ty_session.json"


# -------------------
# RSA 加密（网页登录仅用于首次获取 sessionKey）
# -------------------
BI_RM = list("0123456789abcdefghijklmnopqrstuvwxyz")
B64MAP = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def int2char(a): return BI_RM[a]

def b64tohex(a):
    d, e, c = "", 0, 0
    for x in a:
        if x != "=":
            v = B64MAP.index(x)
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
    encrypted = rsa.encrypt(string.encode(), pubkey)
    return b64tohex(base64.b64encode(encrypted).decode())


# -------------------
# APP 签名
# -------------------
def calc_app_signature(date, sessionKey):
    return hashlib.sha1((date + sessionKey).encode("utf-8")).hexdigest()


# -------------------
# 只用于首次登陆（获取 sessionKey）
# -------------------
def web_login_get_sessionKey(username, password):
    """
    第一次运行：网页登录拿到 sessionKey
    """
    s = requests.Session()
    logger.info("正在进行首次登录以获取 sessionKey ...")

    urlToken = "https://m.cloud.189.cn/udb/udb_login.jsp?pageId=1&pageKey=default&clientType=wap&redirectURL=https://m.cloud.189.cn/zhuanti/2021/shakeLottery/index.html"
    r = s.get(urlToken)
    jump = re.search(r"https?://[^\s'\"]+", r.text).group()
    r = s.get(jump)
    href = re.search(r'<a id="j-tab-login-link"[^>]*href="([^"]+)"', r.text).group(1)
    r = s.get(href)

    captchaToken = re.findall(r"captchaToken' value='(.+?)'", r.text)[0]
    lt = re.findall(r'lt = "(.+?)"', r.text)[0]
    returnUrl = re.findall(r"returnUrl= '(.+?)'", r.text)[0]
    paramId = re.findall(r'paramId = "(.+?)"', r.text)[0]
    j_rsakey = re.findall(r'j_rsaKey" value="(\S+)"', r.text)[0]

    s.headers.update({"lt": lt})

    enc_user = rsa_encode(j_rsakey, username)
    enc_pass = rsa_encode(j_rsakey, password)

    login_url = "https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do"
    data = {
        "appKey": "cloud",
        "accountType": "01",
        "userName": "{RSA}" + enc_user,
        "password": "{RSA}" + enc_pass,
        "validateCode": "",
        "captchaToken": captchaToken,
        "returnUrl": returnUrl,
        "mailSuffix": "@189.cn",
        "paramId": paramId
    }

    r = s.post(login_url, data=data)
    j = r.json()
    if j["result"] != 0:
        raise Exception("登录失败：" + j["msg"])

    redirect = j["toUrl"]
    r = s.get(redirect)

    # 提取 sessionKey
    sk = s.cookies.get("SESSION_KEY")
    if not sk:
        raise Exception("未能从 Cookie 中获取 sessionKey")

    with open(SESSION_FILE, "w") as f:
        json.dump({"sessionKey": sk}, f)

    logger.info("sessionKey 获取成功")
    return sk


# -------------------
# APP 签到（不需要密码）
# -------------------
def app_sign(sessionKey):
    date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    signature = calc_app_signature(date, sessionKey)

    headers = {
        "User-Agent": "Ecloud/8.9.0 (PLK110; ; uc) Android/36",
        "sessionkey": sessionKey,
        "signature": signature,
        "date": date,
        "Accept-Encoding": "gzip"
    }

    url = f"https://api.cloud.189.cn/mkt/userSign.action?rand={int(time.time()*1000)}&clientType=TELEANDROID&version=8.9.0&model=PLK110"
    r = requests.get(url, headers=headers)

    j = r.json()
    if "isSign" in j:
        logger.info(f"签到成功：获得 {j.get('netdiskBonus',0)}M")
    else:
        logger.error("签到失败：" + r.text)


def main():
    # 优先读取已有 sessionKey
    if os.path.exists(SESSION_FILE):
        sk = json.load(open(SESSION_FILE)).get("sessionKey")
    else:
        sk = None

    # 如果没有sessionKey → 登录一次
    if not sk:
        sk = web_login_get_sessionKey(username, password)

    # 使用 APP 接口签到
    try:
        app_sign(sk)
    except:
        logger.error("sessionKey 失效，重新登录...")
        sk = web_login_get_sessionKey(username, password)
        app_sign(sk)


if __name__ == "__main__":
    main()
