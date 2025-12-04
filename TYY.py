import requests
import datetime
import uuid
import json

# -------------------------
# 固定参数（抓包提供）
# -------------------------
PARAM = "7G+qE/ZTFSWww5zQNjpUO77wbxWN3aIjj8+d1HuropPGj1pcQUOw5ee71Ei2pqiiqK9vXpSmfoMNf+wY4UcTY+2tDM54MOUOd7bOOk+pARs="
PKID = "dd2343aea57f49ad95c62b849c5bc312"

SESSION_KEY = "913aebbf-1b46-49cc-9e73-2b90cd36bf50"
SIGNATURE = "8a70a9dd40b5c3a2bad6449727994ebf45e04d05"

EPVER = "2"
EPKEY = "nTiCHhmIsf1YSkA26Mri28TNJQUzPnRG+71Lyf8FDVn3LysIvzCwiQ0qR7sPVy0zfhMjhl7oJZw68Fcqniv5o0M/QKKk6/GZzkqoIwXy+1h6VfJmPVcHJKNj1gRQuSbjk+iGznWs/nfYg+Bs24D28obeoqfVAg0ZDIdh38Bgd68="
EPWAY = "3"

UA = "Ecloud/ 8.9.0 (PLK110; ; uc) Android/36"

# -------------------------
# 通用请求头
# -------------------------
def build_headers():
    now = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    return {
        "Host": "api.cloud.189.cn",
        "User-Agent": UA,
        "sessionKey": SESSION_KEY,
        "signature": SIGNATURE,
        "date": now,
        "epver": EPVER,
        "epkey": EPKEY,
        "epway": EPWAY,
        "x-request-id": str(uuid.uuid4()),
        "Accept-Encoding": "gzip",
        "Content-Type": "text/xml; charset=utf-8",
        "cache-control": "no-cache",
    }

# -------------------------
# 1）校验参数（可选）
# -------------------------
def check_session():
    url = "https://api.cloud.189.cn/getUserInfo.action"
    params = {
        "param": PARAM,
        "pkId": PKID,
    }
    r = requests.get(url, headers=build_headers(), params=params)
    return r.text

# -------------------------
# 2）签到
# -------------------------
def sign():
    url = "https://api.cloud.189.cn/mkt/userSign.action"
    r = requests.get(url, headers=build_headers())
    try:
        data = r.json()
        if data.get("errorCode") == 0:
            bonus = data.get("netdiskBonus", 0)
            return f"签到成功，获得 {bonus}M 空间"
        else:
            return f"签到失败: {data.get('errorMsg')}"
    except Exception:
        return f"签到失败，返回内容: {r.text}"

# -------------------------
# 主流程
# -------------------------
if __name__ == "__main__":
    print("【1】校验参数 → getUserInfo.action")
    resp1 = check_session()
    print(resp1)

    print("\n【2】开始签到 → userSign.action")
    resp2 = sign()
    print(resp2)
