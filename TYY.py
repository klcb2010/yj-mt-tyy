import requests
import json
import time

# ----------------------------
# 你抓包的参数（必须定期更新）
# ----------------------------
PARAM = "BaeZRg4u4ICX4KsxUYpkGZT8zZZ%2B01F2YTsKY9wNV%2FSzgmu7WCYrSLeFAX2h8F%2BXEw%2B0y%2FF1mkm8axZPtQw3XWt698bT9weiCfSuPycVDoY%3D"
PKID = "95a4d2770e364a78aedc93986b321bc5"
SESSION_KEY = "7169e786-1066-4e72-9edc-9bbcb18bc7c2"
SIGNATURE = "aeb17c5ecd0fa27f9f58e96a82c0ab68e3acce54"
DATE = "Thu, 4 Dec 2025 14:19:52 GMT"
EPKEY = "KRbdS2LSc1NQKsgFnmXWq4aWEWkpBz2VHiGgCZ6xtS2NfeoaoGzYBkFQnmEaDa8hMmwmXQdL6FYKzsawIjAMs/VZOfUu15ofwncashNCrvKgjt3YrdZfiBtr1njZbY5u9oR7XsthutQ0czzCh1HXe/N7skFSxvdd4oNcpV+xkS8="
X_REQUEST_ID = "901a5aeb-83c5-4177-b7fe-2e6638cee6d3"


# ==========================================
#  访问 getUserInfo.action 以验证参数是否有效
# ==========================================
def get_user_info():
    url = "https://api.cloud.189.cn/getUserInfo.action"

    params = {
        "param": PARAM,
        "pkId": PKID
    }

    headers = {
        "user-agent": "Ecloud/ 8.9.0 (PLK110; ; uc) Android/36",
        "cache-control": "no-cache",
        "x-request-id": X_REQUEST_ID,
        "sessionkey": SESSION_KEY,
        "signature": SIGNATURE,
        "date": DATE,
        "epver": "2",
        "epkey": EPKEY,
        "epway": "3",
        "accept-encoding": "gzip",
        "content-type": "text/xml; charset=utf-8"
    }

    resp = requests.get(url, headers=headers, params=params)
    return resp.text


# ==========================================
#             天翼云签到接口
#  APP 端使用的是：/sign/commit
# ==========================================
def sign_in():
    url = "https://api.cloud.189.cn/mkt/userSign.action"

    headers = {
        "user-agent": "Ecloud/ 8.9.0 (PLK110; ; uc) Android/36",
        "cache-control": "no-cache",
        "x-request-id": X_REQUEST_ID,
        "sessionkey": SESSION_KEY,
        "signature": SIGNATURE,
        "date": DATE,
        "epver": "2",
        "epkey": EPKEY,
        "epway": "3",
        "accept-encoding": "gzip",
        "content-type": "application/x-www-form-urlencoded"
    }

    resp = requests.post(url, headers=headers)
    return resp.text


# ==========================================
#                    主程序
# ==========================================
def main():
    print("【1】校验参数 → getUserInfo.action")
    info = get_user_info()
    print(info)

    time.sleep(1)

    print("\n【2】开始签到 → userSign.action")
    result = sign_in()
    print(result)


if __name__ == "__main__":
    main()
