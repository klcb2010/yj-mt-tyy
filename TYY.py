#!/usr/bin/python3
# -*- coding: utf-8 -*-   https://e.189.cn/user/account/serviceControl.do 关闭「设备锁」和「唯一ID」校验
​
import time
import re
import json
import base64
import urllib.parse
import rsa
import requests
import random
import os
from datetime import datetime, timedelta
​
# 随机延迟配置（环境变量）
MAX_RANDOM_DELAY = int(os.getenv("MAX_RANDOM_DELAY", "300"))  # 默认最多5分钟
RANDOM_SIGNIN = os.getenv("RANDOM_SIGNIN", "true").lower() == "true"
​
def format_time_remaining(seconds):
    if seconds <= 0:
        return "立即执行"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}小时{minutes}分{secs}秒"
    elif minutes > 0:
        return f"{minutes}分{secs}秒"
    else:
        return f"{secs}秒"
​
def wait_with_countdown(delay_seconds, task_name="任务"):
    if delay_seconds <= 0:
        return
    print(f"⏳ {task_name} 需等待 {format_time_remaining(delay_seconds)}")
    remaining = delay_seconds
    while remaining > 0:
        if remaining <= 10 or remaining % 10 == 0:
            print(f"倒计时: {format_time_remaining(remaining)}")
        sleep_time = 1 if remaining <= 10 else min(10, remaining)
        time.sleep(sleep_time)
        remaining -= sleep_time
​
class TianYiYunPan:
    def __init__(self, username, password, index):
        self.username = username
