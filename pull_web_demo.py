#! /usr/bin/env python
# -*- coding:utf-8 -*-
# 多进程操作
# 从服务器上读取json文件，解析json文件，
# 根据文件中的option属性决定是add还是delete
# 若为add，则读取文件中的图片的url，拉到本地人脸数据库中
# 若为delete，则删除数据库中的相应图片
import requests
import json
import urllib2
import os
import time
from PyQt4 import QtCore

dir = './web_dataset/'

pull = requests.get("http://xx.xx.xx.xx/api/deviceTest?deviceId=yyy")
print pull.text

jsonData = json.loads(pull.text, encoding='utf-8')
l = len(jsonData['list'])
print l

# start = time.time()
# for i in range(1,l):
# 	json = jsonData['list'][i]
# 	userID = json['userId']
# 	name = json['name']
# 	option = json['option']
# 	url = json['url']#获取第一张图片
# 	print url
#
# 	req=urllib2.urlopen(str(url))
# 	buf = req.read()
#
# 	file_name = str(userID) +'_'+ name + '.jpg'
# 	file_dir = os.path.join(dir, file_name)
#
# 	if option == 'add':
#
# 		print file_dir
# 		f=open(file_dir,"wb")
# 		req=urllib2.urlopen(url)
# 		buf=req.read()
# 		f.write(buf)
# 	elif option == 'delete':
# 		if os.path.exists(file_dir):
# 			os.remove(file_dir)
# 		else:
# 			print "no such file:%s"%file_dir
# end =time.time()
# print(u'Use time1 {0} s'.format(end - start))



from  multiprocessing import Pool
import multiprocessing
from multiprocessing import Process


def Pull(i):
    print "this is func{0}:{1}".format(i, time.ctime())
    json = jsonData['list'][i]
    userID = json['userId']
    name = json['name']
    option = json['option']
    url = json['url']  # 获取第一张图片
    print url

    req = urllib2.urlopen(str(url))
    buf = req.read()

    file_name = str(userID) + '_' + name + '.jpg'
    file_dir = os.path.join(dir, file_name)

    if option == 'add':

        print file_dir
        f = open(file_dir, "wb")
        req = urllib2.urlopen(url)
        buf = req.read()
        f.write(buf)
    elif option == 'delete':
        if os.path.exists(file_dir):
            os.remove(file_dir)
        else:
            print "no such file:%s" % file_dir
    print "func{0} finish{1}".format(i, time.ctime())


start = time.time()

pool = Pool(processes=10)
for i in range(1, l):
    pool.apply_async(Pull, (i,))
pool.close()
pool.join()

end = time.time()
print(u'Use time2 {0} s'.format(end - start))
