'''
cron:  0 8 * * *
new Env('MT论坛签到')
'''
import requests
import re
import os
import time
import random
import xml.etree.ElementTree as ET
from notify import send

# 配置
BBS_URL = "https://bbs.binmt.cc/member.php"
SIGN_PAGE_URL = "https://bbs.binmt.cc/k_misign-sign.html"
CREDIT_PAGE_URL = "https://bbs.binmt.cc/home.php?mod=spacecp&ac=credit&showcredit=1"
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0'
]
HEADERS = {
    'User-Agent': random.choice(USER_AGENTS)
}

session = requests.Session()

def get_login_hashes():
    params = {'mod': 'logging', 'action': 'login'}
    try:
        login_res = session.get(url=BBS_URL, headers=HEADERS, params=params, timeout=10)
        login_res.raise_for_status()
        loginhash = re.search(r'loginhash=(.+?)"', login_res.text)
        formhash = re.search(r'name="formhash" value="(.+?)"', login_res.text)
        if not loginhash or not formhash:
            print("登录 loginhash 或 formhash 查找失败")
            send("MT论坛签到失败", "无法获取登录参数")
            return False
        return loginhash.group(1), formhash.group(1)
    except Exception as e:
        print(f"获取登录参数失败: {str(e)}")
        send("MT论坛签到失败", f"获取登录参数失败: {str(e)}")
        return False

def login(loginhash, formhash, username, password, loginfield="username"):
    params = {
        'mod': 'logging', 'action': 'login', 'loginsubmit': 'yes',
        'loginhash': loginhash, 'inajax': '1'
    }
    data = {
        'formhash': formhash, 'loginfield': loginfield,
        'username': username, 'password': password,
        'questionid': '0', 'answer': ''
    }
    try:
        time.sleep(random.uniform(1, 3))  # 随机延迟
        res = session.post(url=BBS_URL, headers=HEADERS, params=params, data=data, timeout=10)
        res.raise_for_status()
        if '欢迎您回来' in res.text or '手机号登录成功' in res.text:
            print('登录成功')
            return True
        else:
            print('登录失败，请检查用户名或密码')
            send("MT论坛签到失败", "登录失败，请检查用户名或密码")
            return False
    except Exception as e:
        print(f"登录请求失败: {str(e)}")
        send("MT论坛签到失败", f"登录请求失败: {str(e)}")
        return False

def get_sign_formhash():
    try:
        time.sleep(random.uniform(1, 3))
        res = session.get(url=SIGN_PAGE_URL, headers=HEADERS, timeout=10)
        res.raise_for_status()
        formhash_match = re.search(r'formhash=([a-f0-9]{8})', res.text)
        if formhash_match:
            return formhash_match.group(1)
        else:
            print("无法获取签到页面的 formhash")
            send("MT论坛签到失败", "无法获取签到页面的 formhash")
            return False
    except Exception as e:
        print(f"获取签到页面失败: {str(e)}")
        send("MT论坛签到失败", f"获取签到页面失败: {str(e)}")
        return False

def get_daily_score():
    try:
        time.sleep(random.uniform(1, 3))
        res = session.get(url=CREDIT_PAGE_URL, headers=HEADERS, timeout=10)
        res.raise_for_status()
        # 提取每日签到金币奖励
        score_match = re.search(r'<td>每日签到</td>\s*<td>金币\s*<span class="xi1">\+(\d+)</span></td>', res.text)
        score = f"{score_match.group(1)} 金币" if score_match else "未知"
        return score, res.text
    except Exception as e:
        print(f"获取积分页面失败: {str(e)}")
        send("MT论坛签到失败", f"获取积分页面失败: {str(e)}")
        return "未知", None

def check_sign_status():
    try:
        time.sleep(random.uniform(1, 3))
        res = session.get(url=SIGN_PAGE_URL, headers=HEADERS, timeout=10)
        res.raise_for_status()
        # 检查是否包含已签到图片
        if re.search(r'come_30\.jpg', res.text):
          
            score, _ = get_daily_score()
            notify_msg = f"今日已签到，得分: {score}"
            print(f"今日得分: {score}")
            send("MT论坛签到", notify_msg)
            return True, score, res.text
        # 检查文本提示
        signed_texts = [
            '您今日已经签到', '已签到', '今日已签到', '已经签到',
            '您已完成今日签到', '今日已签', '已完成签到', '签到已完成',
            '今日已完成签到', '已签', '签到完成', '今日签到已完成'
        ]
        if any(text in res.text for text in signed_texts):
            print("检测到已签到 停止签到动作")
            score, _ = get_daily_score()
            notify_msg = f"今日已签到，得分: {score}"
            print(f"今日得分: {score}")
            send("MT论坛签到", notify_msg)
            return True, score, res.text
        # 从积分页面推断是否已签到
        _, credit_page_text = get_daily_score()
        if credit_page_text and re.search(r'<td>每日签到</td>\s*<td>金币\s*<span class="xi1">\+(\d+)</span></td>', credit_page_text):
           
            score, _ = get_daily_score()
            notify_msg = f"今日已签到，得分: {score}"
            print(f"今日得分: {score}")
            send("MT论坛签到", notify_msg)
            return True, score, res.text
        print("未检测到已签到，继续尝试签到")
        return False, None, res.text
    except Exception as e:
        print(f"检查签到状态失败: {str(e)}")
        send("MT论坛签到失败", f"检查签到状态失败: {str(e)}")
        return False, None, None

def checkinfo(max_retries=3):
    print(f"开始签到尝试: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    # 先检查签到状态
    is_signed, score, sign_page_text = check_sign_status()
    if is_signed:
        print("已签到，跳过签到请求")
        return True

    print("尝试签到请求")
    for attempt in range(max_retries):
        try:
            # 获取动态 formhash
            formhash = get_sign_formhash()
            if not formhash:
                return False

            # 构造签到 URL
            sign_url = f"{SIGN_PAGE_URL}?operation=qiandao&format=button&formhash={formhash}"
            time.sleep(random.uniform(1, 3))
            res = session.get(url=sign_url, headers=HEADERS, timeout=10)
            res.raise_for_status()

            # 检查是否为 XML 响应
            if res.text.startswith('<?xml'):
                try:
                    root = ET.fromstring(res.text)
                    content = root.text or root.find('root').text
                except Exception as e:
                    print(f"解析 XML 失败: {str(e)}")
                    content = res.text
            else:
                content = res.text

            # 检查响应
            signed_texts = [
                '您今日已经签到', '已签到', '今日已签到', '已经签到',
                '您已完成今日签到', '今日已签', '已完成签到', '签到已完成',
                '今日已完成签到', '已签', '签到完成', '今日签到已完成'
            ]
            if any(text in content for text in signed_texts):
                print("今日已签到")
                score, _ = get_daily_score()
                notify_msg = f"今日已签到，得分: {score}"
                print(f"得分: {score}")
                send("MT论坛签到", notify_msg)
                return True
            elif '签到成功' in content:
                print("签到成功")
                score, _ = get_daily_score()
                notify_msg = f"签到成功，得分: {score}"
                print(f"得分: {score}")
                send("MT论坛签到", notify_msg)
                return True
            else:
                print(f"签到失败：未知错误，响应内容: {content[:100]}...")
                send("MT论坛签到失败", f"签到失败，响应内容: {content[:100]}...")
                return False
        except Exception as e:
            print(f"签到请求失败: {str(e)}，尝试 {attempt+1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(5)
            continue
    print("签到失败：达到最大重试次数")
    send("MT论坛签到失败", "签到失败：达到最大重试次数")
    return False

def main():
    print(f"脚本开始运行: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    mt_bbs = os.getenv('MT_BBS')
    if not mt_bbs:
        print("未设置 MT_BBS 环境变量")
        send("MT论坛签到失败", "未设置 MT_BBS 环境变量")
        return
    try:
        username, password = mt_bbs.split(';')
    except ValueError:
        print("MT_BBS 格式错误，应为 '用户名;密码'")
        send("MT论坛签到失败", "MT_BBS 格式错误，应为 '用户名;密码'")
        return
    result = get_login_hashes()
    if not result:
        return
    loginhash, formhash = result
    if not login(loginhash, formhash, username, password):
        return
    checkinfo()

if __name__ == '__main__':
  
  
    main()
