# 原作者 海东青 
#抓包 capacity/growth/info 
#变量值 kps=xxxx；sign=xxxx；vcode=xxxx
# 更新 250524
'''
cron:  5 0 * * *
const $ = new Env("夸克签到");
'''

import os
import re
import sys
import requests

# 可选：Server酱推送
def send_to_server(title, desp):
    server_key = "Server酱KEY"
    if server_key == "Server酱KEY":
        return
    url = f"https://sctapi.ftqq.com/{server_key}.send"
    try:
        requests.post(url, data={"title": title, "desp": desp})
    except:
        pass

# 从环境变量中获取 cookie 列表
def get_env():
    if "QUARK_COOKIE" in os.environ:
        return os.environ.get("QUARK_COOKIE").strip().split('$')
    else:
        msg = '❌ 未配置环境变量 QUARK_COOKIE'
        print(msg)
        send_to_server('夸克自动签到', msg)
        sys.exit(0)

# 单位转换
def convert_bytes(b):
    units = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while b >= 1024 and i < len(units) - 1:
        b /= 1024
        i += 1
    return f"{b:.2f} {units[i]}"

# 签到逻辑
class Quark:
    def __init__(self, user_data):
        self.param = user_data

    def get_growth_info(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        try:
            return requests.get(url=url, params=querystring).json().get("data")
        except:
            return None

    def get_growth_sign(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        data = {"sign_cyclic": True}
        try:
            response = requests.post(url=url, json=data, params=querystring).json()
            if response.get("data"):
                return True, response["data"]["sign_daily_reward"]
            else:
                return False, response.get("message", "未知错误")
        except:
            return False, "请求失败"

    def do_sign(self, user_index):
        info = self.get_growth_info()
        if not info:
            return f"第{user_index}个账号 获取信息失败"

        user = self.param.get("user", "未知用户")
        is_vip = "88VIP" if info.get("88VIP") else "普通用户"
        total = convert_bytes(info["total_capacity"])
        acc = convert_bytes(info["cap_composition"].get("sign_reward", 0)) if "sign_reward" in info["cap_composition"] else "0 MB"

        sign_data = info.get("cap_sign", {})
        if sign_data.get("sign_daily"):
            reward = convert_bytes(sign_data.get("sign_daily_reward", 0))
            progress = f"({sign_data['sign_progress']}/{sign_data['sign_target']})"
            status = f"已签到+{reward}"
        else:
            success, reward = self.get_growth_sign()
            if success:
                reward = convert_bytes(reward)
                progress = f"({sign_data['sign_progress'] + 1}/{sign_data['sign_target']})"
                status = f"签到成功+{reward}"
            else:
                progress = f"({sign_data.get('sign_progress', 0)}/{sign_data.get('sign_target', 7)})"
                status = f"签到失败：{reward}"

        return f"第{user_index}个账号 {is_vip} {user} 网盘总容量：{total}，签到累计容量：{acc} 签到状态：{status}，连签进度{progress}"

# 主程序
def main():
    cookie_quark = get_env()
    print(f"✅ 检测到共 {len(cookie_quark)} 个夸克账号\n")

    msg = ""
    for i, ck in enumerate(cookie_quark):
        user_data = {}
        for item in ck.replace(" ", "").split(';'):
            if '=' in item:
                k, v = item.split('=', 1)
                user_data[k] = v
        log = Quark(user_data).do_sign(i + 1)
        msg += log + '\n'
        print(log)

    send_to_server('夸克自动签到', msg.strip())

if __name__ == "__main__":
    main()
