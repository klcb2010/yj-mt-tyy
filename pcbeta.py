"""
cron: 25 6 * * *
new Env('远景论坛签到');
"""

import requests
import os
import time
import re
from datetime import datetime

# 从环境变量 YJ_BBS 获取用户名和密码
yj_bbs = os.getenv("YJ_BBS")
if not yj_bbs:
    print("错误：请设置环境变量 YJ_BBS，格式为 用户名;密码")
    exit(1)

# 解析用户名和密码
try:
    USERNAME, PASSWORD = yj_bbs.split(";")
except ValueError:
    print("错误：YJ_BBS 格式不正确，应为 用户名;密码")
    exit(1)

# 初始变量
cookies = ""
request = requests.session()
replyMsg = "每日回帖签到"

pcHeaders = {
    "Host": "i.pcbeta.com",
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
}

pcbbsHeaders = {
    "Host": "bbs.pcbeta.com",
    "Connection": "keep-alive",
    "User-Agent": pcHeaders["User-Agent"],
    "Accept": pcHeaders["Accept"],
}

def writeLog(content):
    now = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    log_dir = "./log"
    os.makedirs(log_dir, exist_ok=True)
    log_file = f"{log_dir}/pcBetalog-{now}.html"
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"写入日志失败：{str(e)}")

def save_cookie():
    with open("cookie.txt", "w", encoding="utf-8") as f:
        f.write(cookies)

def load_cookie():
    global cookies, pcHeaders, pcbbsHeaders
    try:
        with open("cookie.txt", "r", encoding="utf-8") as f:
            cookies = f.read().strip()
            pcHeaders["Cookie"] = cookies
            pcbbsHeaders["Cookie"] = cookies
            print("✅ 已从文件加载 Cookie")
    except FileNotFoundError:
        print("⚠️ 未找到 Cookie 文件，需登录")

def login():
    global cookies, pcHeaders, pcbbsHeaders
    login_url = "https://i.pcbeta.com/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&inajax=1"
    login_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "quickforward": "yes",
        "handlekey": "ls",
    }
    headers = pcHeaders.copy()
    headers.update({
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://i.pcbeta.com/member.php?mod=logging&action=login",
    })

    try:
        response = request.post(login_url, data=login_data, headers=headers)
        if "登录成功" in response.text or "succeedhandle_ls" in response.text:
            cookies = "; ".join([f"{k}={v}" for k, v in request.cookies.items()])
            pcHeaders["Cookie"] = cookies
            pcbbsHeaders["Cookie"] = cookies
            print("✅ 登录成功，Cookie 已更新")
            writeLog("登录成功，Cookie: " + cookies)
            return True
        else:
            print("❌ 登录失败，请检查用户名和密码")
            writeLog(response.text)
            return False
    except Exception as e:
        print(f"❌ 登录异常：{str(e)}")
        writeLog(str(e))
        return False

def check_cookie():
    if not cookies:
        print("Cookie 为空，需登录")
        return False
    test_url = "https://i.pcbeta.com/home.php?mod=space"
    try:
        response = request.get(test_url, headers=pcHeaders)
        if "请先登录" in response.text or response.status_code == 403:
            print("Cookie 失效，需重新登录")
            return False
        print("✅ Cookie 有效")
        return True
    except Exception as e:
        print(f"检查 Cookie 异常：{str(e)}")
        return False

def getTaskID():
    try:
        news = request.get(url=newUrl, headers=pcHeaders).text
        doing = request.get(url=doingUrl, headers=pcHeaders).text
        if "回帖打卡" in news:
            return re.search(r'id=(.+?)">回帖打卡', news).group(1)
        elif "回帖打卡" in doing:
            return re.search(r'id=(.+?)">回帖打卡', doing).group(1)
        else:
            writeLog(news + "\n" + doing)
            return False
    except Exception as e:
        writeLog(str(e))
        return False

def getTaskUrl():
    global idd
    idd = getTaskID()
    if not idd:
        return None, None
    try:
        viewRes = request.get(f"https://i.pcbeta.com/home.php?mod=task&do=view&id={idd}", headers=pcHeaders)
        tieUrl = re.search(r'在“<a href="(.+?)">', viewRes.text).group(1)
        replyRes = request.get(tieUrl, headers=pcbbsHeaders)
        fid = re.search(r'fid=(.+?)&', replyRes.text).group(1)
        tid = re.search(r'tid=(.+?)&', replyRes.text).group(1)
        formhash = re.search(r'formhash=(.+?)&', replyRes.text).group(1)
        replyUrl = f"https://bbs.pcbeta.com/forum.php?mod=post&action=reply&fid={fid}&tid={tid}&extra=page=1&replysubmit=yes&infloat=yes&handlekey=fastpost&inajax=1"
        return replyUrl, formhash
    except Exception as e:
        writeLog(viewRes.text)
        return None, None

def pcbetaCheckin():
    if "每日打卡" in newTaskRes:
        taskRes = request.get(url=pcUrl, headers=pcHeaders).text
        if "抱歉，本期您已申请过此任务，请下期再来" in taskRes:
            return "已签到，请勿重复签到"
        elif "恭喜您，任务已成功完成" in taskRes:
            return "签到成功"
        else:
            time.sleep(1)
            lqRes = request.get(url=lqurl+id, headers=pcHeaders).text
            if "任务已成功完成" in lqRes:
                return "签到成功，PB币+1"
            elif "不是进行中的任务" in lqRes:
                doneCheck = request.get(doneUrl, headers=pcHeaders).text
                if "每日打卡" in doneCheck:
                    return "签到已完成"
            writeLog(lqRes)
            return "签到失败"
    elif "每日打卡" in doneTaskRes:
        return "今日已签到"
    else:
        writeLog(newTaskRes + "\n" + doneTaskRes)
        return "签到失败，未找到任务"

def pcbetaReply():
    taskName = "回帖打卡福利"
    if taskName in newTaskRes or taskName in doingRes.text:
        global idd
        idd = getTaskID()
        if not idd:
            return "无法获取任务 ID"
        request.get(f"https://i.pcbeta.com/home.php?mod=task&do=apply&id={idd}", headers=pcHeaders)
        replyUrl, formhash = getTaskUrl()
        if not replyUrl:
            return "获取任务 URL 失败"
        data = {
            "message": replyMsg,
            "posttime": int(time.time()),
            "formhash": formhash,
            "subject": "",
            "usesig": "1"
        }
        resRes = request.post(replyUrl, headers=pcbbsHeaders, data=data)
        if "回复发布成功" in resRes.text:
            request.get(lqurl+idd, headers=pcHeaders)
            done = request.get(doneUrl, headers=pcHeaders)
            if taskName in done.text:
                return "打卡成功，PB币+2"
            else:
                return "奖励领取失败"
        else:
            writeLog(resRes.text)
            return "回帖失败"
    else:
        writeLog(newTaskRes + "\n" + doingRes.text)
        return "没有回帖任务"

if __name__ == "__main__":
    # 链接定义
    pcUrl = "https://i.pcbeta.com/home.php?mod=task&do=apply&id=149"
    lqurl = "https://i.pcbeta.com/home.php?mod=task&do=draw&id="
    newUrl = "https://i.pcbeta.com/home.php?mod=task&item=new"
    doingUrl = "https://i.pcbeta.com/home.php?mod=task&item=doing"
    doneUrl = "https://i.pcbeta.com/home.php?mod=task&item=done"

    # 尝试加载 cookie 文件
    load_cookie()

    # 检查 Cookie 是否有效，否则登录
    if not check_cookie():
        print("尝试重新登录...")
        if not login():
            exit(1)
        save_cookie()

    # 获取任务信息
    try:
        newTaskRes = request.get(newUrl, headers=pcHeaders).text
        doingTaskRes = request.get(doingUrl, headers=pcHeaders).text
        doneTaskRes = request.get(doneUrl, headers=pcHeaders).text
        doingRes = request.get(doingUrl, headers=pcHeaders)
    except Exception as e:
        print(f"任务状态获取失败：{str(e)}")
        exit(1)

    # 执行签到 & 回帖
    checkMsg = pcbetaCheckin()
    replyMsg = pcbetaReply()
    print(f"{checkMsg}\n{replyMsg}")
