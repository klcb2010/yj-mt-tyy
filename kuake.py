# 原作者 海东青 
#抓包 capacity/growth/info 
#变量值 kps=xxxx；sign=xxxx；vcode=xxxx
# 更新 250524
'''
cron:  5 0 * * *
const $ = new Env("夸克签到");
'''

import os
import sys
import requests

def send_to_server(title, desp):
    server_key = ""
    if not server_key:
        return
    try:
        url = f"https://sctapi.ftqq.com/{server_key}.send"
        requests.post(url, data={"title": title, "desp": desp})
    except:
        pass

def convert_bytes(b):
    units = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while b >= 1024 and i < len(units) - 1:
        b /= 1024
        i += 1
    return f"{b:.2f} {units[i]}"

def get_env():
    cookie_env = os.environ.get("QUARK_COOKIE")
    if not cookie_env:
        print('❌ 未配置环境变量 QUARK_COOKIE')
        send_to_server('夸克签到', '❌ 未配置环境变量 QUARK_COOKIE')
        sys.exit(1)
    return cookie_env.strip().split('$')

class Quark:
    def __init__(self, raw_cookie, user_index):
        self.index = user_index
        self.cookie = raw_cookie
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13)",
            "Cookie": raw_cookie
        }

    def get_growth_info(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            return r.json().get("data", {})
        except:
            return {}

    def get_growth_sign(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
        try:
            r = requests.post(url, headers=self.headers, json={"sign_cyclic": True}, timeout=10)
            res = r.json()
            if res.get("data"):
                return True, res["data"].get("sign_daily_reward", 0)
            return False, res.get("message", "未知错误")
        except:
            return False, "请求失败"

    def do_sign(self):
        info = self.get_growth_info()
        if not info:
            return f"第{self.index}个账号 获取信息失败"

        nickname = info.get("user_name", "未知用户")
        total = convert_bytes(info.get("total_capacity", 0))
        sign_total = convert_bytes(info.get("cap_composition", {}).get("sign_reward", 0))
        sign_data = info.get("cap_sign", {})
        signed = sign_data.get("sign_daily", False)
        progress = f"({sign_data.get('sign_progress', 0)}/{sign_data.get('sign_target', 7)})"

        if signed:
            reward = convert_bytes(sign_data.get("sign_daily_reward", 0))
            status = f"签到状态：已签到 +{reward}"
        else:
            success, reward = self.get_growth_sign()
            if success:
                reward = convert_bytes(reward)
                sign_data["sign_progress"] = sign_data.get("sign_progress", 0) + 1
                progress = f"({sign_data['sign_progress']}/{sign_data.get('sign_target', 7)})"
                status = f"签到状态：签到成功 +{reward}"
            else:
                status = f"签到状态：签到失败 {reward}"

        return f"第{self.index}个账号 {nickname} 网盘总容量：{total} 签到累计容量：{sign_total} {status} 连签进度：{progress}"

def main():
    result = []
    cookies = get_env()
    for idx, ck in enumerate(cookies):
        quark = Quark(ck, idx + 1)
        result.append(quark.do_sign())
    final = "\n".join(result)
    print(final)
    send_to_server("夸克网盘签到结果", final)

if __name__ == "__main__":
    main()
