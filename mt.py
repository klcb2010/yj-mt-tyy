#原作者 https://raw.githubusercontent.com/linbailo/zyqinglong/refs/heads/main/mt.py
#修改于2025 05 06  mtluntan=username1&password1@username2&password2@username3&password3

'''
cron:  5 0 * * *
const $ = new Env("MT论坛");
'''
import requests
import re
import os
import time
import random

# 设置UA
ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'
session = requests.session()

# 打印
def myprint(msg):
    print(msg)

# 通知
def send_notification_message(title):
    try:
        from sendNotify import send
        send(title, ''.join(all_print_list))
    except Exception:
        pass

# 判断网络
def pdwl():
    try:
        ipdi = requests.get('http://ifconfig.me/ip', timeout=6).text.strip()
        dizhi = f'http://ip-api.com/json/{ipdi}?lang=zh-CN'
        pdip = requests.get(url=dizhi, timeout=6).json()
        country = pdip['country']
    except Exception:
        pass

try:
    pdwl()
except Exception:
    pass

# 主流程
def main(username, password):
    headers = {'User-Agent': ua}
    session.get('https://bbs.binmt.cc', headers=headers)
    chusihua = session.get(
        'https://bbs.binmt.cc/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login',
        headers=headers
    )

    try:
        loginhash = re.findall('loginhash=(.*?)">', chusihua.text)[0]
        formhash = re.findall('formhash" value="(.*?)".*? />', chusihua.text)[0]
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

    # 每个账号登录前的延迟
    time.sleep(random.uniform(10, 20))

    denlu = session.post(headers=headers, url=denurl, data=data).text
    if '欢迎您回来' in denlu:
        fzmz = re.findall('欢迎您回来，(.*?)，现在', denlu)[0]
        username_only = fzmz.split(' ', 1)[-1] if ' ' in fzmz else fzmz
        myprint(f'{username_only}：登录成功')

        zbqd = session.get('https://bbs.binmt.cc/k_misign-sign.html', headers=headers).text
        formhash = re.findall('formhash" value="(.*?)".*? />', zbqd)[0]

        qdurl = f'https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&format=text&formhash={formhash}'
        qd = session.get(url=qdurl, headers=headers).text

        qdyz = re.findall('<root><!$CDATA$$(.*?)$$$></root>', qd)
        myprint(f'签到状态：{qdyz[0] if qdyz else "未知"}')

        if '已签' in qd:
            huoqu(formhash)
    return True

# 获取签到奖励
def huoqu(formhash):
    headers = {'User-Agent': ua}
    huo = session.get('https://bbs.binmt.cc/k_misign-sign.html', headers=headers).text
    jiang = re.findall('id="lxreward" value="(.*?)">', huo)
    myprint(f'签到奖励：{jiang[0] if jiang else "无"}金币')
    tuic = f'https://bbs.binmt.cc/member.php?mod=logging&action=logout&formhash={formhash}'
    session.get(url=tuic, headers=headers)

# 主执行
if __name__ == '__main__':
    username = ''
    password = ''
    all_print_list = []

    if 'mtluntan' in os.environ:
        fen = os.environ.get("mtluntan").split("@")
        for duo in fen:
            if "&" not in duo:
                continue
            username, password = duo.split("&", 1)
            try:
                success = main(username, password)
                if not success:
                    for _ in range(2):
                        time.sleep(3)
                        if main(username, password):
                            break
            except Exception as e:
                myprint(f'{username}：出错，原因：{str(e)}')

            # 多账号之间延迟（防止风控）
            time.sleep(random.uniform(5, 15))
    else:
        if username and password:
            try:
                success = main(username, password)
                if not success:
                    for _ in range(2):
                        time.sleep(3)
                        if main(username, password):
                            break
            except Exception:
                pass
        else:
            exit()

    try:
        send_notification_message(title='mt论坛')
    except Exception:
        pass
