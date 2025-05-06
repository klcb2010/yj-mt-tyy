#!/usr/bin/python3
# -- coding: utf-8 --
# -------------------------------
# @Author : github@arvinsblog https://github.com/arvinsblog/deepsea
# @Time : 2025-3-19 13:30:25
# 收集和修复能用的脚本
# 修正说明中的变量名 2025 05 06
"""
打开小程序或APP-我的-积分, 捉以下几种url之一,把整个url放到变量 SFSY （对 修正的就是这里）里,多账号换行分割
小程序抓包后筛选 activityRedirect?source=
"""
# cron:  0 10,15,18 * * *
# const $ = new Env("顺丰速运");
import hashlib
import json
import os
import random
import time
import re
from datetime import datetime, timedelta
from sys import exit
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

IS_DEV = False

# 邀请ID列表（移除空字符串）
inviteId = [
    '7B0443273B2249CB9CDB7B48B94DEC13',
    '809FAF1E02D045D7A0DB185E5C91CFB1'
]

class RUN:
    def __init__(self, info, index):
        split_info = info.split('@')
        url = split_info[0]
        len_split_info = len(split_info)
        last_info = split_info[len_split_info - 1]
        self.send_UID = None
        if len_split_info > 0 and "UID_" in last_info:
            self.send_UID = last_info
        self.index = index + 1
        print(f"\n---------开始执行第{self.index}个账号>>>>>")
        self.s = requests.session()
        self.s.verify = False
        self.headers = {
            'Host': 'mcs-mimp-web.sf-express.com',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090551) XWEB/6945 Flue',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'zh-CN,zh',
            'platform': 'MINI_PROGRAM',
        }
        self.anniversary_black = False
        self.member_day_black = False
        self.member_day_red_packet_drew_today = False
        self.member_day_red_packet_map = {}
        self.login_res = self.login(url)
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.answer = False
        self.max_level = 8
        self.packet_threshold = 1 << (self.max_level - 1)

    def get_deviceId(self, characters='abcdef0123456789'):
        result = ''
        for char in 'xxxxxxxx-xxxx-xxxx':
            if char == 'x':
                result += random.choice(characters)
            elif char == 'X':
                result += random.choice(characters).upper()
            else:
                result += char
        return result

    def login(self, sfurl):
        try:
            ress = self.s.get(sfurl, headers=self.headers)
            self.user_id = self.s.cookies.get_dict().get('_login_user_id_', '')
            self.phone = self.s.cookies.get_dict().get('_login_mobile_', '')
            self.mobile = self.phone[:3] + "*" * 4 + self.phone[7:] if self.phone else ''
            if self.phone:
                print(f'用户:【{self.mobile}】登陆成功')
                return True
            else:
                print('获取用户信息失败')
                return False
        except Exception as e:
            print(f'登录失败: {e}')
            return False

    def getSign(self):
        timestamp = str(int(round(time.time() * 1000)))
        token = 'wwesldfs29aniversaryvdld29'
        sysCode = 'MCS-MIMP-CORE'
        data = f'token={token}×tamp={timestamp}&sysCode={sysCode}'
        signature = hashlib.md5(data.encode()).hexdigest()
        data = {
            'sysCode': sysCode,
            'timestamp': timestamp,
            'signature': signature
        }
        self.headers.update(data)
        return data

    def do_request(self, url, data={}, req_type='post'):
        self.getSign()
        try:
            if req_type.lower() == 'get':
                response = self.s.get(url, headers=self.headers)
            elif req_type.lower() == 'post':
                response = self.s.post(url, headers=self.headers, json=data)
            else:
                raise ValueError('Invalid req_type: %s' % req_type)
            res = response.json()
            return res
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f'Request failed: {e}')
            return None

    def sign(self):
        print(f'>>>>>>开始执行签到')
        json_data = {"comeFrom": "vioin", "channelFrom": "WEIXIN"}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~integralTaskSignPlusService~automaticSignFetchPackage'
        response = self.do_request(url, data=json_data)
        if response and response.get('success'):
            count_day = response.get('obj', {}).get('countDay', 0)
            if response.get('obj') and response['obj'].get('integralTaskSignPackageVOList'):
                packet_name = response["obj"]["integralTaskSignPackageVOList"][0]["packetName"]
                print(f'>>>签到成功，获得【{packet_name}】，本周累计签到【{count_day + 1}】天')
            else:
                print(f'今日已签到，本周累计签到【{count_day + 1}】天')
        else:
            error_message = response.get('errorMessage') if response else '无返回'
            print(f'签到失败！原因：{error_message}')

    def superWelfare_receiveRedPacket(self):
        print(f'>>>>>>超值福利签到')
        json_data = {'channel': 'czflqflqdlhbxcx'}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberActLengthy~redPacketActivityService~superWelfare~receiveRedPacket'
        try:
            response = self.do_request(url, data=json_data)
            if response and response.get('success'):
                gift_list = response.get('obj', {}).get('giftList', [])
                extra_gift_list = response.get('obj', {}).get('extraGiftList', [])
                gift_list.extend(extra_gift_list)
                gift_names = ', '.join([gift['giftName'] for gift in gift_list]) or '无奖励'
                receive_status = response.get('obj', {}).get('receiveStatus')
                status_message = '领取成功' if receive_status == 1 else '已领取过'
                print(f'超值福利签到[{status_message}]: {gift_names}')
            else:
                error_message = response.get('errorMessage') or json.dumps(response) or '无返回'
                print(f'超值福利签到失败: {error_message}')
        except Exception as e:
            print(f'超值福利签到发生错误: {str(e)}')

    def get_SignTaskList(self, END=False):
        if not END:
            print(f'>>>开始获取签到任务列表')
        json_data = {
            'channelType': '1',
            'deviceId': self.get_deviceId(),
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~integralTaskStrategyService~queryPointTaskAndSignFromES'
        response = self.do_request(url, data=json_data)
        if response and response.get('success') and response.get('obj'):
            totalPoint = response["obj"].get("totalPoint", 0)
            if END:
                print(f'当前积分：【{totalPoint}】')
            else:
                print(f'执行前积分：【{totalPoint}】')
            for task in response["obj"].get("taskTitleLevels", []):
                self.taskId = task["taskId"]
                self.taskCode = task["taskCode"]
                self.strategyId = task["strategyId"]
                self.title = task["title"]
                status = task["status"]
                skip_title = ['用行业模板寄件下单', '去新增一个收件偏好', '参与积分活动']
                if status == 3:
                    print(f'>{self.title}-已完成')
                    continue
                if self.title in skip_title:
                    print(f'>{self.title}-跳过')
                    continue
                else:
                    self.doTask()
                    time.sleep(3)
                    self.receiveTask()

    def doTask(self):
        print(f'>>>开始去完成【{self.title}】任务')
        json_data = {'taskCode': self.taskCode}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonRoutePost/memberEs/taskRecord/finishTask'
        response = self.do_request(url, data=json_data)
        if response and response.get('success'):
            print(f'>【{self.title}】任务-已完成')
        else:
            error_message = response.get('errorMessage') or '无返回'
            print(f'>【{self.title}】任务-{error_message}')

    def receiveTask(self):
        print(f'>>>开始领取【{self.title}】任务奖励')
        json_data = {
            "strategyId": self.strategyId,
            "taskId": self.taskId,
            "taskCode": self.taskCode,
            "deviceId": self.get_deviceId()
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~integralTaskStrategyService~fetchIntegral'
        response = self.do_request(url, data=json_data)
        if response and response.get('success'):
            print(f'>【{self.title}】任务奖励领取成功！')
        else:
            error_message = response.get('errorMessage') or '无返回'
            print(f'>【{self.title}】任务-{error_message}')

    def do_honeyTask(self):
        json_data = {"taskCode": self.taskCode}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberEs~taskRecord~finishTask'
        response = self.do_request(url, data=json_data)
        if response and response.get('success'):
            print(f'>【{self.taskType}】任务-已完成')
        else:
            error_message = response.get('errorMessage') or '无返回'
            print(f'>【{self.taskType}】任务-{error_message}')

    def receive_honeyTask(self):
        print('>>>执行收取丰蜜任务')
        self.headers['syscode'] = 'MCS-MIMP-CORE'
        self.headers['channel'] = 'wxwdsj'
        self.headers['accept'] = 'application/json, text/plain, */*'
        self.headers['content-type'] = 'application/json;charset=UTF-8'
        self.headers['platform'] = 'MINI_PROGRAM'
        json_data = {"taskType": self.taskType}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~receiveHoney'
        response = self.do_request(url, data=json_data)
        if response and response.get('success'):
            print(f'收取任务【{self.taskType}】成功！')
        else:
            error_message = response.get('errorMessage') or '无返回'
            print(f'收取任务【{self.taskType}】失败！原因：{error_message}')

    def get_coupom(self):
        print('>>>执行领取生活权益领券任务')
        json_data = {
            "from": "Point_Mall",
            "orderSource": "POINT_MALL_EXCHANGE",
            "goodsNo": self.goodsNo,
            "quantity": 1,
            "taskCode": self.taskCode
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberGoods~pointMallService~createOrder'
        response = self.do_request(url, data=json_data)
        if response and response.get('success'):
            print(f'>领券成功！')
        else:
            error_message = response.get('errorMessage') or '无返回'
            print(f'>领券失败！原因：{error_message}')

    def get_coupom_list(self):
        print('>>>获取生活权益券列表')
        json_data = {
            "memGrade": 1,
            "categoryCode": "SHTQ",
            "showCode": "SHTQWNTJ"
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberGoods~mallGoodsLifeService~list'
        response = self.do_request(url, data=json_data)
        if response and response.get('success'):
            goodsList = response.get("obj", [{}])[0].get("goodsList", [])
            for goods in goodsList:
                exchangeTimesLimit = goods.get('exchangeTimesLimit', 0)
                if exchangeTimesLimit >= 7:
                    self.goodsNo = goods['goodsNo']
                    print(f'当前选择券号：{self.goodsNo}')
                    self.get_coupom()
                    break
        else:
            error_message = response.get('errorMessage') or '无返回'
            print(f'>领券失败！原因：{error_message}')

    def get_honeyTaskListStart(self):
        print('>>>开始获取采蜜换大礼任务列表')
        json_data = {}
        self.headers['channel'] = 'wxwdsj'
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~taskDetail'
        response = self.do_request(url, data=json_data)
        if response and response.get('success'):
            for item in response.get("obj", {}).get("list", []):
                self.taskType = item["taskType"]
                status = item["status"]
                if status == 3:
                    print(f'>【{self.taskType}】-已完成')
                    if self.taskType == 'BEES_GAME_TASK_TYPE':
                        self.bee_need_help = False
                    continue
                if "taskCode" in item:
                    self.taskCode = item["taskCode"]
                    if self.taskType == 'DAILY_VIP_TASK_TYPE':
                        self.get_coupom_list()
                    else:
                        self.do_honeyTask()
                if self.taskType == 'BEES_GAME_TASK_TYPE':
                    self.honey_damaoxian()
                time.sleep(2)

    def honey_damaoxian(self):
        print('>>>执行大冒险任务')
        gameNum = 5
        for i in range(1, gameNum + 1):
            json_data = {'gatherHoney': 20}
            print(f'>>开始第{i}次大冒险')
            url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeGameService~gameReport'
            response = self.do_request(url, data=json_data)
            if response and response.get('success'):
                gameNum = response.get('obj', {}).get('gameNum', 0)
                print(f'>大冒险成功！剩余次数【{gameNum}】')
                time.sleep(2)
            elif response and response.get("errorMessage") == '容量不足':
                print(f'> 需要扩容')
                self.honey_expand()
            else:
                error_message = response.get("errorMessage") if response else '无返回'
                print(f'>大冒险失败！【{error_message}】')
                break

    def honey_expand(self):
        print('>>>容器扩容')
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~expand'
        response = self.do_request(url, data={})
        if response and response.get('success'):
            obj = response.get('obj', {})
            print(f'>成功扩容【{obj}】容量')
        else:
            error_message = response.get('errorMessage') or '无返回'
            print(f'>扩容失败！【{error_message}】')

    def honey_indexData(self, END=False):
        if not END:
            print('\n>>>>>>>开始执行采蜜换大礼任务')
        valid_invites = [invite for invite in inviteId if invite and invite != self.user_id]
        if not valid_invites:
            print("没有可用的 inviteId，跳过邀请")
            return
        random_invite = random.choice(valid_invites)
        self.headers['channel'] = 'wxwdsj'
        json_data = {"inviteUserId": random_invite}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~indexData'
        response = self.do_request(url, data=json_data)
        if response and response.get('success'):
            usableHoney = response.get('obj', {}).get('usableHoney', 0)
            if END:
                print(f'当前丰蜜：【{usableHoney}】')
            else:
                print(f'执行前丰蜜：【{usableHoney}】')
            taskDetail = response.get('obj', {}).get('taskDetail', [])
            activityEndTime = response.get('obj', {}).get('activityEndTime', '')
            try:
                activity_end_time = datetime.strptime(activityEndTime, "%Y-%m-%d %H:%M:%S")
                current_time = datetime.now()
                if current_time.date() == activity_end_time.date():
                    print("本期活动今日结束，请及时兑换")
                else:
                    print(f'本期活动结束时间【{activityEndTime}】')
            except ValueError:
                print(f"活动结束时间格式错误: {activityEndTime}")
            for task in taskDetail:
                self.taskType = task['type']
                self.receive_honeyTask()
                time.sleep(2)

    def main(self):
        try:
            wait_time = random.randint(1000, 3000) / 1000.0
            time.sleep(wait_time)
            if not self.login_res:
                return False
            self.sign()
            self.superWelfare_receiveRedPacket()
            self.get_SignTaskList()
            self.get_SignTaskList(True)
            self.honey_indexData()
            self.get_honeyTaskListStart()
            self.honey_indexData(True)
            target_time = datetime(2025, 4, 8, 19, 0)
            if datetime.now() < target_time:
                self.EAR_END_2023_TaskList()
                self.EAR_END_2023_query()
            else:
                print('周年庆活动已结束')
            current_date = datetime.now().day
            if 26 <= current_date <= 28:
                self.member_day_index()
            else:
                print('未到指定时间不执行会员日任务')
            if self.MIDAUTUMN_2024_index():
                self.MIDAUTUMN_2024_weeklyGiftStatus()
                self.MIDAUTUMN_2024_coinStatus()
                self.MIDAUTUMN_2024_taskList()
                self.MIDAUTUMN_2024_coinStatus(True)
            return True
        except Exception as e:
            print(f"执行账号 {self.index} 失败: {e}")
            return False

def get_quarter_end_date():
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    next_quarter_first_day = datetime(current_year, ((current_month - 1) // 3 + 1) * 3 + 1, 1)
    quarter_end_date = next_quarter_first_day - timedelta(days=1)
    return quarter_end_date.strftime("%Y-%m-%d")

def is_activity_end_date(end_date):
    current_date = datetime.now().date()
    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    return current_date == end_date

def down_file(filename, file_url):
    print(f'开始下载：{filename}，下载地址：{file_url}')
    try:
        response = requests.get(file_url, verify=False, timeout=10)
        response.raise_for_status()
        with open(filename + '.tmp', 'wb') as f:
            f.write(response.content)
        print(f'【{filename}】下载完成！')
        temp_filename = filename + '.tmp'
        if os.path.exists(temp_filename):
            if os.path.exists(filename):
                os.remove(filename)
            os.rename(temp_filename, filename)
            print(f'【{filename}】重命名成功！')
            return True
        else:
            print(f'【{filename}】临时文件不存在！')
            return False
    except Exception as e:
        print(f'【{filename}】下载失败：{str(e)}')
        return False

if __name__ == '__main__':
    APP_NAME = '顺丰速运'
    ENV_NAME = 'SFSY'
    CK_NAME = 'url'
    print(f'''
{APP_NAME}脚本
    ''')
    if ENV_NAME in os.environ:
        tokens = re.split("@|#|\n", os.environ.get(ENV_NAME))
    elif "sfsyUrl" in os.environ:
        print("调用拉菲变量")
        tokens = re.split("@|#|\n", os.environ.get("sfsyUrl"))
    else:
        tokens = ['']
        print(f'无{ENV_NAME}变量')
    local_version = '2024.06.02'
    if len(tokens) > 0:
        print(f"\n>>>>>>>>>>共获取到{len(tokens)}个账号<<<<<<<<<<")
        for index, infos in enumerate(tokens):
            if not infos.strip():
                continue
            run_result = RUN(infos, index).main()
            if not run_result:
                continue
