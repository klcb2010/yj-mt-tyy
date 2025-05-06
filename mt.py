#原作者 https://raw.githubusercontent.com/linbailo/zyqinglong/refs/heads/main/mt.py
#修改于2025 05 06

import requests
import re
import os
import time

# 设置ua
ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'
session = requests.session()

def myprint(msg):
    print(msg)

def send_notification_message(title):
    try:
        from sendNotify import send
        send(title, ''.join(all_print_list))
    except Exception:
        pass

try:
    if didibb == True:
        pass
    else:
        pass
except Exception:
    pass

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

def main(username, password):
    headers = {'User-Agent': ua}
    session.get('https://bbs.binmt.cc', headers=headers)
    chusihua = session.get('https://bbs.binmt.cc/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login', headers=headers)
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
    denlu = session.post(headers=headers, url=denurl, data=data).text
    
    if '欢迎您回来' in denlu:
        fzmz = re.findall('欢迎您回来，(.*?)，现在', denlu)[0]
        # 去除用户级别（如“博士生”或“大学生”），假设级别和用户名以空格分隔
        username_only = fzmz.split(' ', 1)[-1] if ' ' in fzmz else fzmz
        myprint(f'{username_only}：登录成功')
        zbqd = session.get('https://bbs.binmt.cc/k_misign-sign.html', headers=headers).text
        formhash = re.findall('formhash" value="(.*?)".*? />', zbqd)[0]
        qdurl = f'https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&format=text&formhash={formhash}'
        qd = session.get(url=qdurl, headers=headers).text
        qdyz = re.findall('<root><!\[CDATA\[(.*?)\]\]></root>', qd)[0]
        myprint(f'签 到 状 态：{qdyz}')
        if '已签' in qd:
            huoqu(formhash)
    return True

def huoqu(formhash):
    headers = {'User-Agent': ua}
    huo = session.get('https://bbs.binmt.cc/k_misign-sign.html', headers=headers).text
    jiang = re.findall('id="lxreward" value="(.*?)">', huo)[0]
    myprint(f'签 到 奖 励：{jiang}金币')
    tuic = f'https://bbs.binmt.cc/member.php?mod=logging&action=logout&formhash={formhash}'
    session.get(url=tuic, headers=headers)

if __name__ == '__main__':
    username = ''
    password = ''
    if 'mtluntan' in os.environ:
        fen = os.environ.get("mtluntan").split("@")
        for duo in fen:
            username, password = duo.split("&")
            try:
                main(username, password)
            except Exception:
                pdcf = False
                pdcf1 = 1
                while not pdcf and pdcf1 <= 3:
                    pdcf = main(username, password)
                    pdcf1 += 1
    else:
        if username == '' or password == '':
            exit()
        else:
            try:
                main(username, password)
            except Exception:
                pdcf = False
                pdcf1 = 1
                while not pdcf and pdcf1 <= 3:
                    pdcf = main(username, password)
                    pdcf1 += 1
    try:
        send_notification_message(title='mt论坛')
    except Exception:
        pass
