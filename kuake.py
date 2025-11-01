# 原作者 海东青 
#抓包 capacity/growth/info   个人信息获取失败 重新抓包
#变量值 kps=xxxx；sign=xxxx；vcode=xxxx
# 更新 250526
'''
cron:  5 0 * * *
const $ = new Env("夸克签到");
'''

import os
import sys
import requests

# Server酱推送（可选，未配置可忽略）
def send_to_server(title, desp):
    server_key = os.environ.get("PUSH_KEY", "")
    if not server_key:
        return
    url = f"https://sctapi.ftqq.com/{server_key}.send"
    data = {"title": title, "desp": desp}
    try:
        requests.post(url, data=data)
    except:
        pass

def get_env():
    if "QUARK_COOKIE" in os.environ:
        return os.environ.get("QUARK_COOKIE").split('$')
    else:
        print("未配置 QUARK_COOKIE 环境变量")
        send_to_server("夸克签到失败", "未配置 QUARK_COOKIE 环境变量")
        sys.exit(1)

class Quark:
    def __init__(self, user_data):
        self.param = user_data

    def convert_bytes(self, b):
        units = ("B", "KB", "MB", "GB", "TB", "PB")
        i = 0
        while b >= 1024 and i < len(units) - 1:
            b /= 1024
            i += 1
        return f"{b:.2f} {units[i]}"

    def get_growth_info(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        query = {
            "pr": "ucpro", "fr": "android",
            "kps": self.param.get("kps"),
            "sign": self.param.get("sign"),
            "vcode": self.param.get("vcode")
        }
        resp = requests.get(url, params=query).json()
        return resp.get("data", False)

    def get_growth_sign(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
        query = {
            "pr": "ucpro", "fr": "android",
            "kps": self.param.get("kps"),
            "sign": self.param.get("sign"),
            "vcode": self.param.get("vcode")
        }
        data = {"sign_cyclic": True}
        resp = requests.post(url, params=query, json=data).json()
        if resp.get("data"):
            return True, resp["data"]["sign_daily_reward"]
        else:
            return False, resp.get("message", "未知错误")

    def do_sign(self):
        log = ""
        info = self.get_growth_info()
        username = self.param.get("user", "")

        log += f"{username}\n"

        if not info:
            log += "签到失败：获取成长信息失败\n"
            return log

        total = self.convert_bytes(info["total_capacity"])
        signed = self.convert_bytes(info["cap_composition"].get("sign_reward", 0))
        log += f"网盘总容量：{total}\n"
        log += f"签到累计容量：{signed}\n"

        if info["cap_sign"]["sign_daily"]:
            today = self.convert_bytes(info["cap_sign"]["sign_daily_reward"])
            log += f"签到状态：已签到+{today}\n"
            log += f"连签进度({info['cap_sign']['sign_progress']}/{info['cap_sign']['sign_target']})\n"
        else:
            ok, result = self.get_growth_sign()
            if ok:
                today = self.convert_bytes(result)
                progress = info['cap_sign']['sign_progress'] + 1
                target = info['cap_sign']['sign_target']
                log += f"签到状态：签到成功+{today}\n"
                log += f"连签进度({progress}/{target})\n"
            else:
                log += f"签到失败：{result}\n"

        return log

def main():
    cookies = get_env()
    all_log = ""

    for idx, ck in enumerate(cookies):
        user_data = {}
        for kv in ck.strip().split(';'):
            if '=' in kv:
                k, v = kv.split('=', 1)
                user_data[k.strip()] = v.strip()

        all_log += f"第{idx + 1}个账号："
        all_log += Quark(user_data).do_sign()
        all_log += "\n"

    print(all_log.strip())
    send_to_server("夸克自动签到", all_log.strip())

if __name__ == "__main__":
    main()
