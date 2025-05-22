#原作者 https://raw.githubusercontent.com/linbailo/zyqinglong/refs/heads/main/mt.py
#修改于2025 05 20  mtluntan=username1&password1@username2&password2@username3&password3

'''
cron:  5 0 * * *
const $ = new Env("MT论坛");
'''
import requests
import re
import os
import time
import random

# 设置 UA
ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'
session = requests.session()

all_print_list = []

def myprint(msg):
    print(msg)
    all_print_list.append(str(msg) + "\n")

# 推送通知
def send_notification_message(title):
    try:
        from sendNotify import send
        send(title, ''.join(all_print_list))
    except Exception:
        pass

# 判断网络是否在国内
def pdwl():
    try:
        ipdi = requests.get('http://ifconfig.me/ip', timeout=6).text.strip()
        dizhi = f'http://ip-api.com/json/{ipdi}?lang=zh-CN'
        pdip = requests.get(url=dizhi, timeout=6).json()
        country = pdip['country']
    except Exception:
        pass

def main(username, password):
    headers = {'User-Agent': ua}
    session.get('https://bbs.binmt.cc', headers=headers)

    # 获取登录页面并提取 loginhash 和 formhash
    chusihua = session.get(
        'https://bbs.binmt.cc/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login',
        headers=headers)
    try:
        loginhash = re.findall('loginhash=(.*?)">', chusihua.text)[0]
        formhash = re.findall('formhash" value="(.*?)"', chusihua.text)[0]
    except Exception:
        return False

    denurl = f'https://bbs.binmt.cc/member.php?mod=logging&action=login&loginsubmit=yes&handlekey=login&loginhash={loginhash}&inajax=1'
    data = {
        'formhash': formhash,
        'referer': 'https://bbs.binmt.cc/forum.php',
        'loginfield': 'username',
        'username': username,
        'password': password,
        'questionid': '0',
        'answer': '',
    }

    # 登录前延迟
    time.sleep(random.uniform(10, 20))

    denlu = session.post(headers=headers, url=denurl, data=data).text
    if '欢迎您回来' in denlu:
        fzmz = re.findall('欢迎您回来，(.*?)，现在', denlu)[0]
        username_only = fzmz.split(' ', 1)[-1] if ' ' in fzmz else fzmz
        myprint(f'{username_only}：登录成功')

        zbqd = session.get('https://bbs.binmt.cc/k_misign-sign.html', headers=headers).text
        formhash = re.findall('formhash" value="(.*?)"', zbqd)[0]
        qdurl = f'https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&format=text&formhash={formhash}'

        qd = session.get(url=qdurl, headers=headers).text
        qdyz = re.findall(r'<!\[CDATA\[(.*?)\]\]>', qd)
        myprint(f'签到状态：{qdyz[0] if qdyz else "未知"}')

        if '已签' in qd or '成功' in qd:
            huoqu(formhash)

        return True
    else:
        myprint(f'{username}：登录失败')
        return False

# 获取签到奖励并退出登录
def huoqu(formhash):
    headers = {'User-Agent': ua}
    huo = session.get('https://bbs.binmt.cc/k_misign-sign.html', headers=headers).text
    jiang = re.findall('id="lxreward" value="(.*?)">', huo)
    myprint(f'签到奖励：{jiang[0] if jiang else "未知"}金币')
    tuic = f'https://bbs.binmt.cc/member.php?mod=logging&action=logout&formhash={formhash}'
    session.get(url=tuic, headers=headers)

if __name__ == '__main__':
    username = ''
    password = ''

    if 'mtluntan' in os.environ:
        fen = os.environ.get("mtluntan").split("@")
        for i, duo in enumerate(fen):
            username, password = duo.split("&")

            # 每个账号间增加延迟
            if i != 0:
                time.sleep(random.uniform(5, 10))

            try:
                result = main(username, password)
            except Exception:
                result = False

            retry = 1
            while not result and retry <= 3:
                result = main(username, password)
                retry += 1
    else:
        if username == '' or password == '':
            exit()
        else:
            try:
                result = main(username, password)
            except Exception:
                result = False

            retry = 1
            while not result and retry <= 3:
                result = main(username, password)
                retry += 1

    try:
        send_notification_message(title='mt论坛')
    except Exception:
        pass
