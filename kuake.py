import os
import sys
import requests

# 可选推送函数（Server酱）
def send_to_server(title, desp):
    server_key = "Server酱KEY"  # 替换为你自己的 Server 酱 KEY，留空则不推送
    if server_key == "Server酱KEY":
        return
    try:
        url = f"https://sctapi.ftqq.com/{server_key}.send"
        requests.post(url, data={"title": title, "desp": desp})
    except:
        pass

# 单位转换
def convert_bytes(b):
    units = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while b >= 1024 and i < len(units) - 1:
        b /= 1024
        i += 1
    return f"{b:.2f} {units[i]}"

# 读取 QUARK_COOKIE 环境变量
def get_env():
    cookie_env = os.environ.get("QUARK_COOKIE")
    if not cookie_env:
        print('❌ 未配置环境变量 QUARK_COOKIE')
        send_to_server('夸克签到', '❌ 未配置环境变量 QUARK_COOKIE')
        sys.exit(1)
    return cookie_env.strip().split('$')

class Quark:
    def __init__(self, param, user_index):
        self.param = param
        self.user_index = user_index

    def get_growth_info(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        try:
            return requests.get(url, params={**self.param, "pr": "ucpro", "fr": "android"}).json().get("data", {})
        except:
            return {}

    def get_growth_sign(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
        try:
            resp = requests.post(url, params={**self.param, "pr": "ucpro", "fr": "android"}, json={"sign_cyclic": True}).json()
            if "data" in resp:
                return True, resp["data"]["sign_daily_reward"]
            return False, resp.get("message", "未知错误")
        except:
            return False, "接口异常"

    def do_sign(self):
        info = self.get_growth_info()
        if not info:
            return f"第{self.user_index}个账号 获取信息失败\n"

        nickname = info.get("user_name", "未知用户")
        total = convert_bytes(info.get("total_capacity", 0))
        accumulated = convert_bytes(info.get("accumulate_capacity", 0))
        sign_data = info.get("cap_sign", {})
        signed = sign_data.get("sign_daily", False)
        progress_day = sign_data.get("sign_days", 0)
        progress_cycle = sign_data.get("sign_cycle_days", 7)

        if signed:
            reward = convert_bytes(sign_data.get("sign_daily_reward", 0))
            status = f"已签到 +{reward}"
        else:
            success, reward = self.get_growth_sign()
            if success:
                reward = convert_bytes(reward)
                status = f"签到成功 +{reward}"
            else:
                status = f"签到失败：{reward}"

        return (
            f"第{self.user_index}个账号 {nickname}\n"
            f"网盘总容量：{total}\n"
            f"签到累计容量：{accumulated}\n"
            f"签到状态：{status}\n"
            f"连签进度：({progress_day}/{progress_cycle})\n"
        )

def main():
    logs = []
    cookies = get_env()
    for idx, ck in enumerate(cookies):
        kv = dict(i.split("=", 1) for i in ck.split(";") if "=" in i)
        q = Quark(kv, idx + 1)
        logs.append(q.do_sign())
    final_log = "\n".join(logs)
    print(final_log)
    send_to_server("夸克网盘签到结果", final_log)

if __name__ == "__main__":
    main()
