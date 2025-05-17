"""
cron: 2 0 * * *
new Env('远景论坛签到')
"""
import requests
from datetime import datetime
import time
import re
import html
import notify
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

request = requests.session()

# 回帖内容
replyMsg = "每日回帖签到"

pcUrl = "https://i.pcbeta.com/home.php?mod=task&do=apply&id=149"
pcHeaders = {
    "Host": "i.pcbeta.com",
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
}

pcbbsHeaders = {
    "Host": "bbs.pcbeta.com",
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
}

def getToken(u, p):
    loginUrl = "https://bbs.pcbeta.com/member.php?mod=logging&action=login"
    try:
        loginPage = request.get(url=loginUrl, headers=pcHeaders).text
        # 查找loginhash
        loginhash_match = re.search(r'loginhash=(.+?)">', loginPage)
        if not loginhash_match:
            logging.error("无法找到 loginhash")
            return False
        loginhash = loginhash_match.group(1)
        # 查找formhash
        formhash_match = re.search(r'name="formhash" value="(.+?)" />', loginPage)
        if not formhash_match:
            logging.error("无法找到 formhash")
            return False
        formhash = formhash_match.group(1)

        url = "https://bbs.pcbeta.com/member.php"
        param = {
            "mod": "logging",
            "action": "login",
            "loginsubmit": "yes",
            "loginhash": loginhash,
            "inajax": "1"
        }
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            "Connection": "keep-alive",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://bbs.pcbeta.com/member.php?mod=logging&action=login",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
        data = {
            "formhash": formhash,
            "loginfield": "username",
            "username": u,
            "password": p
        }
        res = request.post(url=url, headers=header, data=data, params=param)
        if "欢迎您回来" in res.text:
            logging.info("登录成功")
            cookies = requests.utils.dict_from_cookiejar(request.cookies)
            return cookies
        else:
            logging.error("登录失败")
            logging.debug(res.text)
            return False
    except Exception as e:
        logging.error(f"登录过程中发生错误: {str(e)}")
        return False

def writeLog(file):
    time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_dir = "./log"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = f"{log_dir}/pcBetalog-{time_str}.html"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(file)
    logging.info(f"日志已保存到 {log_file}")

def pcbetaCheckin():
    try:
        if "每日打卡" in newTaskRes:
            # 开始执行签到
            taskRes = request.get(url=pcUrl, headers=pcHeaders).text
            if "抱歉，本期您已申请过此任务，请下期再来" in taskRes:
                return "已签到，请勿重复签到"
            elif "恭喜您，任务已成功完成" in taskRes:
                return "签到成功"
            else:
                time.sleep(1)
                lqRes = request.get(url=lqurl+"149", headers=pcHeaders).text
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
            return "没有找到每日打卡任务"
    except Exception as e:
        logging.error(f"签到过程中发生错误: {str(e)}")
        return "签到失败"

def getTaskUrl(idd):
    try:
        # 获取任务贴URL
        viewRes = request.get(url=f"https://i.pcbeta.com/home.php?mod=task&do=view&id={idd}", headers=pcHeaders).text
        tieUrl_match = re.search(r'在“<a href="(.+?)">', viewRes)
        if not tieUrl_match:
            logging.error("无法找到任务贴 URL")
            return False, False
        tieUrl = tieUrl_match.group(1)
        replyRes = request.get(url=tieUrl, headers=pcbbsHeaders).text
        # 获取fid
        fid_match = re.search(r'fid=(.+?)&', replyRes)
        if not fid_match:
            logging.error("无法找到 fid")
            return False, False
        fid = fid_match.group(1)
        # 获取tid
        tid_match = re.search(r'tid=(.+?)&', replyRes)
        if not tid_match:
            logging.error("无法找到 tid")
            return False, False
        tid = tid_match.group(1)
        # 获取formhash
        formhash_match = re.search(r'formhash=(.+?)&', replyRes)
        if not formhash_match:
            logging.error("无法找到 formhash")
            return False, False
        formhash = formhash_match.group(1)
        replyUrl = f"https://bbs.pcbeta.com/forum.php?mod=post&action=reply&fid={fid}&tid={tid}&extra=page=1&replysubmit=yes&infloat=yes&handlekey=fastpost&inajax=1"
        return replyUrl, formhash
    except Exception as e:
        logging.error(f"获取任务 URL 过程中发生错误: {str(e)}")
        return False, False

def getTaskID():
    try:
        news = request.get(url=newUrl, headers=pcHeaders).text
        doing = request.get(url=doingUrl, headers=pcHeaders).text
        id_match = None
        if "回帖打卡" in news:
            id_match = re.search(r'id=(.+?)">回帖打卡', news)
        elif "回帖打卡" in doing:
            id_match = re.search(r'id=(.+?)">回帖打卡', doing)
        if id_match:
            return id_match.group(1)
        logging.error("未找到回帖打卡任务")
        return False
    except Exception as e:
        logging.error(f"获取任务 ID 过程中发生错误: {str(e)}")
        return False

def pcbetaReply():
    taskName = "回帖打卡福利"
    try:
        if taskName in newTaskRes or taskName in doingRes.text:
            # 获取任务id
            idd = getTaskID()
            if not idd:
                return "无法获取任务 ID"
            # 申请回帖打卡任务
            reRes = request.get(url=f"https://i.pcbeta.com/home.php?mod=task&do=apply&id={idd}", headers=pcHeaders).text
            if "任务申请成功" in reRes:
                replyUrl, formhash = getTaskUrl(idd)
                if not replyUrl or not formhash:
                    return "无法获取回帖 URL 或 formhash"
                # 回复帖子
                data = {
                    "message": replyMsg,
                    "posttime": int(time.time()),
                    "formhash": formhash,
                    "subject": "",
                    "usesig": "1"
                }
                resRes = request.post(url=replyUrl, headers=pcbbsHeaders, data=data).text
                if "回复发布成功" in resRes:
                    # 领取奖励
                    lqRes1 = request.get(url=lqurl+idd, headers=pcHeaders).text
                    # 获取任务状态
                    doneTaskRes1 = request.get(url=doneUrl, headers=pcHeaders).text
                    if taskName in doneTaskRes1:
                        return "打卡成功，PB币+2"
                    else:
                        writeLog(lqRes1)
                        return "奖励领取失败"
                else:
                    writeLog(resRes)
                    return "回帖失败"
            else:
                writeLog(reRes)
                return "打卡任务申请失败"
        elif taskName in doneTaskRes:
            return "今日已完成回帖打卡"
        else:
            return "没有回帖打卡任务"
    except Exception as e:
        logging.error(f"回帖打卡过程中发生错误: {str(e)}")
        return "回帖打卡失败"

if __name__ == "__main__":
    # 从环境变量 YJ_BBS 中获取用户名和密码
    yj_bbs = os.getenv('YJ_BBS')
    
    if not yj_bbs:
        logging.error("请设置 YJ_BBS 环境变量，格式为 username;password")
        exit(1)
    
    try:
        # 按分号拆分用户名和密码
        u, p = yj_bbs.split(';')
        if not u or not p:
            raise ValueError("YJ_BBS 格式错误，缺少用户名或密码")
    except ValueError:
        logging.error("YJ_BBS 格式错误，正确格式为 username;password")
        exit(1)
    
    cookie = getToken(u, p)
    if not cookie:
        logging.error("无法获取登录 cookie，程序退出")
        exit(1)
    
    # 领取奖励链接
    lqurl = "https://i.pcbeta.com/home.php?mod=task&do=draw&id="
    # 获取新任务链接
    newUrl = "https://i.pcbeta.com/home.php?mod=task&item=new"
    # 获取进行中的任务链接
    doingUrl = "https://i.pcbeta.com/home.php?mod=task&item=doing"
    # 查看已完成任务链接
    doneUrl = "https://i.pcbeta.com/home.php?mod=task&item=done"
    
    # 获取签到状态信息
    newTaskRes = request.get(url=newUrl, headers=pcHeaders).text
    doingTaskRes = request.get(url=doingUrl, headers=pcHeaders).text
    doneTaskRes = request.get(url=doneUrl, headers=pcHeaders).text
    doingRes = request.get(url=doingUrl, headers=pcHeaders)
    
    checkMsg = pcbetaCheckin()
    replyMsg = pcbetaReply()
    
    logging.info(f"签到结果: {checkMsg}")
    logging.info(f"回帖结果: {replyMsg}")
    # notify.send("远景论坛签到", f"{checkMsg}\n{replyMsg}")
