#! /usr/bin/env python
# -*- coding:utf-8 -*-
# 遍历本地face_detect目录下的图片(确保一个id一段时间内只有一张图片截图保存)
# 将其所有图片name组成列表，传给服务器
# !!!!注意time.time()得到的数据还要再乘1000，并转换成long类型
import requests
import json
import urllib2
import re
import os
import time

# UserId_time，device_id
# push_url 上传链接
push_url = "http://xx.xx.xx.xx/api/device/record"
# userID_+str(time.time()*1000)
list=['1_2222321.jpg']
list.append('3_4342424.jpg')
dict = {'data':list,"deviceId":"xxxx"}

r=requests.post(push_url,data=dict)
print r.text
