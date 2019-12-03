# -*- coding:utf-8 -*-
from PyQt4.QtCore import *
import time


class Through(QThread):
    through_lists = []# 保存通过该门禁的用户信息:ID+time
    pass_sign = pyqtSignal(str)# 设置线程之间传递的信号

    def __init__(self):
        super(Through, self).__init__()

    def inputFRResult(self, result, faceExist):
        self.result = result
        self.faceExist = faceExist

    def run(self):
        if self.faceExist is True:
            if self.result.faceID is None:
                return
            elif self.result.faceID == 'Unknown':
                return
            elif self.result.faceName == 'Unknown':
                return

            elif self.result.faceName == 'Unknow':
                return

            # 如果置信度小于0.5则不能通过
            elif self.result.p < 0.5:
                print(self.result.faceName + ' can not Pass')

            # 否则通过，并记录通过人的姓名和日期时间
            else:
                print(str(time.ctime())+' PASS Name: '+str(self.result.faceName))
                self.pass_sign.emit('PASS')

                self.through_lists.append(str(self.result.faceID)+'_'+str(time.time()))
                print(str(self.result.faceID)+'_'+str(time.time()))
                time.sleep(5)




