"""
cron: 25 6 * * *
new Env('远景论坛签到');
"""
import requests
import os
import time
import re
import html
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

# 初始 Cookie
cookies = ""
request = requests.session()

# 回帖内容
replyMsg = "每日回帖签到"

pcUrl = "https://i.pcbeta.com/home.php?mod=task&do=apply&id=149"
pcHeaders = {
    "Host": "i.pcbeta.com",
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
}

pcbbsHeaders = {
    "Host": "bbs.pcbeta.com",
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
}

# 登录函数
def login():
    global cookies, pcHeaders, pcbbsHeaders
    login_url = "https://i.pcbeta.com/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&inajax=1"
    login_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "quickforward": "yes",
        "handlekey": "ls",
    }
    headers = {
        "Host": "i.pcbeta.com",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://i.pcbeta.com/member.php?mod=logging&action=login",
    }
    
    try:
        response = request.post(login_url, data=login_data, headers=headers)
        if "登录成功" in response.text or "succeedhandle_ls" in response.text:
            cookies = "; ".join([f"{key}={value}" for key, value in request.cookies.items()])
            pcHeaders["Cookie"] = cookies
            pcbbsHeaders["Cookie"] = cookies
            print("登录成功，Cookie 已更新")
            writeLog(f"登录成功，Cookie: {cookies}")
            return True
        else:
            print("登录失败，请检查用户名和密码")
            writeLog(response.text)
            return False
    except Exception as e:
        print(f"登录失败：{str(e)}")
        writeLog(str(e))
        return False

# 检查 Cookie 是否有效
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
        print("Cookie 有效")
        return True
    except Exception as e:
        print(f"检查 Cookie 失败：{str(e)}")
        writeLog(str(e))
        return False

def writeLog(file):
    time = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    log_dir = "./log"
    log_file = f"{log_dir}/pcBetalog-{time}.html"
    try:
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(file)
    except Exception as e:
        print(f"写入日志失败：{str(e)}")

def pcbetaCheckin():
    id = "149"
    if "每日打卡" in newTaskRes:
        # 开始执行签到
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
            if "不是进行中的任务" in lqRes:
                # 检查是否签到成功
                doneTaskRes_check = request.get(url=doneUrl, headers=pcHeaders).text
                if "每日打卡" in doneTaskRes_check:
                    return "签到已完成"
                else:
                    return "签到失败"
            else:
                writeLog(lqRes)
                return "签到失败，具体情况请查看日志"
    elif "每日打卡" in doneTaskRes:
        return "今日已签到，重复签到"
    else:
        print("未找到每日打卡任务")
        writeLog(newTaskRes + "\n" + doneTaskRes)
        return "签到失败，未找到任务"

def getTaskUrl():
    global idd
    idd = getTaskID()
    if not idd:
        print("无法获取任务 ID")
        return None, None
    # 获取任务贴URL
    viewRes = request.get(url=f"https://i.pcbeta.com/home.php?mod=task&do=view&id={idd}", headers=pcHeaders)
    try:
        tieUrl = re.search(r'在“<a href="(.+?)">', viewRes.text).group(1)
        replyRes = request.get(url=tieUrl, headers=pcbbsHeaders)
        # 获取fid
        fid = re.search(r'fid=(.+?)&', replyRes.text).group(1)
        # 获取tid
        tid = re.search(r'tid=(.+?)&', replyRes.text).group(1)
        formhash = re.search(r'formhash=(.+?)&', replyRes.text).group(1)
        replyUrl = f"https://bbs.pcbeta.com/forum.php?mod=post&action=reply&fid={fid}&tid={tid}&extra=page=1&replysubmit=yes&infloat=yes&handlekey=fastpost&inajax=1"
        print(f"")
        return replyUrl, formhash
    except Exception as e:
        print(f"获取任务 URL 失败：{str(e)}")
        writeLog(viewRes.text)
        return None, None

def getTaskID():
    try:
        news = request.get(url=newUrl, headers=pcHeaders).text
        doing = request.get(url=doingUrl, headers=pcHeaders).text
        if "回帖打卡" in news:
            idd = re.search(r'id=(.+?)">回帖打卡', news).group(1)
            print(f"")
            return idd
        elif "回帖打卡" in doing:
            idd = re.search(r'id=(.+?)">回帖打卡', doing).group(1)
            print(f"")
            return idd
        else:
            print("未找到回帖打卡任务")
            writeLog(news + "\n" + doing)
            return False
    except Exception as e:
        print(f"获取任务 ID 失败：{str(e)}")
        writeLog(str(e))
        return False

def pcbetaReply():
    taskName = "回帖打卡福利"
    if taskName in newTaskRes:
        # 获取任务id
        global idd
        idd = getTaskID()
        if not idd:
            return "无法获取任务 ID"
        # 申请回帖打卡任务
        reRes = request.get(url=f"https://i.pcbeta.com/home.php?mod=task&do=apply&id={idd}", headers=pcHeaders)
        if "任务申请成功" in reRes.text:
            result = getTaskUrl()
            if not result[0]:
                return "获取任务 URL 失败"
            # 回复帖子
            data = {
                "message": replyMsg,
                "posttime": int(time.time()),
                "formhash": result[1],
                "subject": "",
                "usesig": "1"
            }
            resRes = request.post(url=result[0], headers=pcbbsHeaders, data=data)
            if "回复发布成功" in resRes.text:
                # 领取奖励
                lqRes1 = request.get(url=lqurl+idd, headers=pcHeaders)
                # 获取任务状态
                doneTaskRes1 = request.get(url=doneUrl, headers=pcHeaders)
                if taskName in doneTaskRes1.text:
                    return "打卡成功，PB币+2"
                else:
                    writeLog(lqRes1.text)
                    return "奖励领取失败"
            else:
                writeLog(resRes.text)
                return "回帖失败"
        else:
            writeLog(reRes.text)
            return "打卡任务申请失败"
    elif taskName in doingRes.text:
        result = getTaskUrl()
        if not result[0]:
            return "获取任务 URL 失败"
        # 回复帖子
        data = {
            "message": replyMsg,
            "posttime": int(time.time()),
            "formhash": result[1],
            "subject": "",
            "usesig": "1"
        }
        resRes = request.post(url=result[0], headers=pcbbsHeaders, data=data)
        if "回复发布成功" in resRes.text:
            # 领取奖励
            lqRes1 = request.get(url=lqurl+idd, headers=pcHeaders)
            # 获取任务状态
            doneTaskRes1 = request.get(url=doneUrl, headers=pcHeaders)
            if taskName in doneTaskRes1.text:
                return "打卡成功，PB币+2"
            else:
                writeLog(lqRes1.text)
                return "奖励领取失败"
        else:
            writeLog(resRes.text)
            return "回帖失败"
    else:
        print("未找到回帖打卡福利任务")
        writeLog(newTaskRes + "\n" + doingRes.text)
        return "没有此任务"

if __name__ == "__main__":
    # 领取奖励链接
    lqurl = "https://i.pcbeta.com/home.php?mod=task&do=draw&id="
    # 获取新任务链接
    newUrl = "https://i.pcbeta.com/home.php?mod=task&item=new"
    # 获取进行中的任务链接
    doingUrl = "https://i.pcbeta.com/home.php?mod=task&item=doing"
    # 查看已完成任务链接
    doneUrl = "https://i.pcbeta.com/home.php?mod=task&item=done"
    
    # 设置初始 Cookie（如果有）
    if cookies:
        pcHeaders["Cookie"] = cookies
        pcbbsHeaders["Cookie"] = cookies
    else:
        # 如果没有 Cookie，直接登录
        if not login():
            print("无法登录，退出")
            exit(1)
    
    # 获取签到状态信息
    try:
        newTaskRes = request.get(url=newUrl, headers=pcHeaders).text
        doingTaskRes = request.get(url=doingUrl, headers=pcHeaders).text
        doneTaskRes = request.get(url=doneUrl, headers=pcHeaders).text
        doingRes = request.get("https://i.pcbeta.com/home.php?mod=task&item=doing", headers=pcHeaders)
    except Exception as e:
        print(f"获取任务状态失败，可能 Cookie 无效：{str(e)}")
        if not check_cookie() and not login():
            print("无法登录，退出")
            exit(1)
        newTaskRes = request.get(url=newUrl, headers=pcHeaders).text
        doingTaskRes = request.get(url=doingUrl, headers=pcHeaders).text
        doneTaskRes = request.get(url=doneUrl, headers=pcHeaders).text
        doingRes = request.get("https://i.pcbeta.com/home.php?mod=task&item=doing", headers=pcHeaders)
    
    # 执行签到和回帖
    checkMsg = pcbetaCheckin()
    replyMsg = pcbetaReply()
    print(f"{checkMsg}\n{replyMsg}")
