# -*- coding:utf-8 -*-

import socket
# from PyQt4 import QtCore, QtGui
# from PyQt4.QtGui import *
from PyQt4.QtCore import *

import requests
import json
import urllib2
import os
import time
from FaceBase import *
from ui import AFRFace
from multiprocessing import Pool

import sys
reload(sys)
sys.setdefaultencoding('utf-8')




class ConnectSever(QThread):
    change = pyqtSignal(list)# 定义信号change

    def __init__(self):
        super(ConnectSever, self).__init__()
        self.list = []
        self.setFacebase()
        self.updatelists = []

    def inputUploadData(self, listdata):
        self.list.append(listdata)

    def setFacebase(self):
        self.arcEngine = AFRFace()

    # do download
    def Pull(self, i=0, data=None, dir='./web_dataset/'):
        print('************************************************')
        # pull = requests.get("http://118.25.20.88/api/deviceTest?deviceId=1Q8VRHO6G51T&code=100")
        # print pull.text
        # jsonData = json.loads(pull.text, encoding='utf-8')
        jsonData = data
        l = len(jsonData['list'])
        print l
        print "this is func{0}:{1}".format(i, time.ctime())
        jsondata = jsonData['list'][i]
        userID = str(jsondata['userId'])

        name = jsondata['name'].decode('utf-8')
        option = jsondata['option'].decode('utf-8')
        url = jsondata['url']  # 获取第一张图片
        print url

        # req = urllib2.urlopen(str(url))
        # buf = req.read()
        if not os.path.exists(dir):
            os.mkdir(dir)
        file_name = str(userID) + '_' + '.jpg'
        file_dir = os.path.join(dir, file_name)

        if option == 'add':# 若从服务器读取的op为add，则添加该人脸图片到本地

            print file_dir
            with open(file_dir, "wb") as f:
                req = urllib2.urlopen(str(url))
                buf = req.read()
                f.write(buf)

            self.updatelists.append({'ID': str(userID), 'name': str(name), 'pic_path': str(file_dir), 'option': 'add'})

            while True:
                try:
                    # 添加一条该人脸图片的信息到pkl中
                    self.arcEngine.addFaceFeature(ID=str(userID).encode('utf-8'), pic_path=str(file_dir), name=str(name), age='Unknown', gender='Unknown')
                    print('success add face info' + str(userID)+'__'+str(name))
                    # self.arcEngine.facebase.savefacedata()

                    break
                except Exception as e:
                    print(e)
                    print('Exception in Connect_Sever.py line 72')
                    time.sleep(5)

        elif option == 'delete':
            self.arcEngine.facebase.removeFaceFeature(ID=str(userID))
            self.arcEngine.facebase.savefacedata()
            self.updatelists.append({'ID': str(userID), 'name': str(name), 'pic_path': str(file_dir), 'option': 'delete'})
            print('success delete ID{}'+str(userID))
            if os.path.exists(file_dir):
                os.remove(file_dir)
            else:
                print "no such file:%s" % file_dir
        print "func{0} finish{1}".format(i, time.ctime())


        print('******************************************************')

    def download(self, processes=10):
        start = time.time()

        # pool = Pool(processes=processes)
        try:
            pull = requests.get("http://xx.xx.xx.xx/api/device?deviceId=yy")
        except Exception as e:
            print(e.message)
        finally:
            print pull.text
        jsonData = json.loads(pull.text, encoding='utf-8')
        l = len(jsonData['list'])
        if l <= 0:
            return

        for i in range(1, l):
            self.Pull(i, jsonData)
            # pool.apply_async(self.Pull, (i,))
        # pool.close()
        # pool.join()
        if l > 0:
            # self.emit(QtCore.SIGNAL('updatefacebase()'))
            self.arcEngine.updatefacebase = True

        end = time.time()
        print(u'Use time2 {0} s'.format(end - start))



    def loading(self, i = 0, data = None, dir = './web_dataset/'):
        print('************************************************')

        jsonData = data
        l = len(jsonData['list'])
        print l
        # print "this is func{0}:{1}".format(i, time.ctime())
        jsondata = jsonData['list'][i]
        userID = str(jsondata['userId'])

        name = jsondata['name'].decode('utf-8')
        option = jsondata['option'].decode('utf-8')
        url = jsondata['url']  # 获取第一张图片
        print url

        # req = urllib2.urlopen(str(url))
        # buf = req.read()
        if not os.path.exists(dir):
            os.mkdir(dir)
        file_name = str(userID) + '_' + '.jpg'
        file_dir = os.path.join(dir, file_name)

        self.updatelists.append({'ID': str(userID), 'name': str(name), 'pic_path': str(file_dir), 'option': option})

    # do upload
    def push(self):

        # 记录 组成列表，传给服务器
        # !!!!注意time.time()得到的数据还要再乘1000，并转换成long类型
        push_url = "http://xx.xx.xx.xx/api/device/record"
        # userID_+str(time.time()*1000)
        # list = ['1_2222321.jpg']
        # list.append('3_4342424.jpg')
        list = self.list
        dict = {'data': list, "deviceId": "1Q8VRHO6G51T"}
        print('----------------------->>>>>><<<<<<<<<<<<<----------------------')

        try:
            if len(dict['data']) > 0:
                r = requests.post(push_url, data=dict)
                print r.text
                print('success upload list')
                self.list = []
        except Exception as e:
            print(e.message)
            print('fill upload data')

    def link(self):
        try:
            pull = requests.get("http://xx.xx.xx.xx/api/device?deviceId=yy")
        except Exception as e:
            print(e.message)
        finally:
            print pull.text
        jsonData = json.loads(pull.text, encoding='utf-8')
        l = len(jsonData['list'])

        if l <= 0:
            return

        for i in xrange(l):
            jsondata = jsonData['list'][i]
            # userID = str(jsondata['userId'])
            # option = jsondata['option'].decode('utf-8')
            self.loading(i, jsonData)# 读取json文件，将需要改变的图片(ID\name\pic_path\option)添加到updatelist中

        self.change.emit(self.updatelists)# 发射信号



    def getAllList(self):

        try:
            pull = requests.get("http://xx.xx.xx.xx/api/device?deviceId=yy")
        except Exception as e:
            print(e.message)
        finally:
            print pull.text
        jsonData = json.loads(pull.text, encoding='utf-8')
        l = len(jsonData['list'])

        if l <= 0:
            return

        for i in xrange(l):
            jsondata = jsonData['list'][i]
            userID = str(jsondata['userId'])
            option = jsondata['option'].decode('utf-8')
            if not self.arcEngine.facebase.hasID(userID):
                self.Pull(i, jsonData)# 从服务器pull图片到本地
                self.arcEngine.updatefacebase = True
            elif option == 'delete':
                self.Pull(i, jsonData)
                self.arcEngine.updatefacebase = True
        # self.change.emit(self.updatelists)



    def run(self):
        self.push()#　将通过门禁的用户记录push到服务器上
        self.link()# 将服务器需要对图片进行的操作数据更新到updatelist中
        self.getAllList()# 正式从服务器pull图片到本地
        # self.download(2)
        time.sleep(60)
