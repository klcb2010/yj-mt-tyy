#原作者 https://raw.githubusercontent.com/linbailo/zyqinglong/refs/heads/main/mt.py
#修改于2025 05 20  mtluntan=username1&password1@username2&password2@username3&password3

"""
cron:  5 0 * * *
const $ = new Env("MT论坛");
"""

#修改于2025 07 05  mtluntan=username1&password1@username2&password2@username3&password3

import requests
import re
import os
import time
import random

ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'
all_print_list = []

def myprint(msg):
    print(msg)
    all_print_list.append(str(msg) + "\n")

def send_notification_message(title):
    try:
        from sendNotify import send
        send(title, ''.join(all_print_list))
    except Exception:
        pass

def cookie_file(username):
    return f'mt_cookie_{username}.txt'

def save_cookie(username, session):
    with open(cookie_file(username), 'w', encoding='utf-8') as f:
        f.write(requests.utils.dict_from_cookiejar(session.cookies).__str__())

def load_cookie(username, session):
    try:
        with open(cookie_file(username), 'r', encoding='utf-8') as f:
            cookie_str = f.read().strip()
            cookies_dict = eval(cookie_str)
            session.cookies = requests.utils.cookiejar_from_dict(cookies_dict)
            myprint(f'{username}：已加载本地 Cookie')
            return True
    except:
        myprint(f'{username}：未找到 Cookie 或 Cookie 文件损坏')
        return False

def check_cookie_valid(session):
    try:
        test = session.get('https://bbs.binmt.cc/k_misign-sign.html', headers={'User-Agent': ua}, timeout=10)
        return 'formhash' in test.text and '签到' in test.text
    except:
        return False

def login_and_sign(username, password, session):
    headers = {'User-Agent': ua}
    session.get('https://bbs.binmt.cc', headers=headers)

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

    time.sleep(random.uniform(5, 10))

    denlu = session.post(headers=headers, url=denurl, data=data).text
    if '欢迎您回来' in denlu:
        fzmz = re.findall('欢迎您回来，(.*?)，现在', denlu)[0]
        uname = fzmz.split(' ', 1)[-1] if ' ' in fzmz else fzmz
        myprint(f'{uname}：登录成功')
        save_cookie(username, session)

        zbqd = session.get('https://bbs.binmt.cc/k_misign-sign.html', headers=headers).text
        formhash = re.findall('formhash" value="(.*?)"', zbqd)[0]
        qdurl = f'https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&format=text&formhash={formhash}'
        qd = session.get(url=qdurl, headers=headers).text
        qdyz = re.findall(r'<!\[CDATA\[(.*?)\]\]>', qd)
        myprint(f'签到状态：{qdyz[0] if qdyz else "未知"}')

        if '已签' in qd or '成功' in qd:
            huoqu(session, formhash)

        return True
    else:
        myprint(f'{username}：登录失败')
        return False

def huoqu(session, formhash):
    headers = {'User-Agent': ua}
    huo = session.get('https://bbs.binmt.cc/k_misign-sign.html', headers=headers).text
    jiang = re.findall('id="lxreward" value="(.*?)">', huo)
    myprint(f'签到奖励：{jiang[0] if jiang else "未知"}金币')
    tuic = f'https://bbs.binmt.cc/member.php?mod=logging&action=logout&formhash={formhash}'
    session.get(url=tuic, headers=headers)

def run_for_account(username, password):
    session = requests.Session()
    headers = {'User-Agent': ua}

    # 优先尝试读取 cookie
    if load_cookie(username, session) and check_cookie_valid(session):
        myprint(f'{username}：Cookie 有效，直接签到')
        try:
            zbqd = session.get('https://bbs.binmt.cc/k_misign-sign.html', headers=headers).text
            formhash = re.findall('formhash" value="(.*?)"', zbqd)[0]
            qdurl = f'https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&format=text&formhash={formhash}'
            qd = session.get(url=qdurl, headers=headers).text
            qdyz = re.findall(r'<!\[CDATA\[(.*?)\]\]>', qd)
            myprint(f'签到状态：{qdyz[0] if qdyz else "未知"}')

            if '已签' in qd or '成功' in qd:
                huoqu(session, formhash)
        except Exception as e:
            myprint(f'{username}：签到失败，尝试重新登录')
            login_and_sign(username, password, session)
    else:
        login_and_sign(username, password, session)

if __name__ == '__main__':
    if 'mtluntan' in os.environ:
        fen = os.environ.get("mtluntan").split("@")
        for i, duo in enumerate(fen):
            username, password = duo.split("&")
            if i != 0:
                time.sleep(random.uniform(5, 10))
            run_for_account(username, password)
    else:
        myprint("环境变量 mtluntan 未设置，格式应为 username1&password1@username2&password2...")
        exit(0)

    try:
        send_notification_message(title='mt论坛')
    except Exception:
        pass
