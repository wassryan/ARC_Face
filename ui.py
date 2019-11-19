# -*- encoding=utf-8 -*-

from my_untils.FaceBase import *
from AFR_face import *
from arcsoft import AFD_FSDKLibrary
# from Connect_Sever import *
from my_untils.throughDoor import *
import sys
import cv2
import numpy as np
from time import sleep
import dlib
from imutils import face_utils
from my_untils.eye_blink import *
from my_untils.search_compare import *
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *
from PyQt4.QtCore import *
# from PyQt4 import phonon
# from PyQt4.QtSql import *
import sys


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8


    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

APPID = c_char_p(b'FBmQrBiFKgDS4UenPAXXSmH4mWXSd6V5oq4yFc17YynT')
FD_SDKKEY = c_char_p(b'C4wd8EyQjD57EPbXuPmSBLjxwJpRMJPb66HjuwWitHE7')
FR_SDKKEY = c_char_p(b'C4wd8EyQjD57EPbXuPmSBLkTaus8JFvgpQRxuvRHQcC3')
FD_WORKBUF_SIZE = 20 * 1024 * 1024
FR_WORKBUF_SIZE = 40 * 1024 * 1024
MAX_FACE_NUM = 50
bUseYUVFile = False
bUseBGRToEngine = True


class AFRFace(QThread):
    updatefacebase = False# 一个flag，是否需要更新本地数据库
    updatelists = []#　从服务器获得的数据(ID\name\pic_path\option)
    facebase = FaceBase()# 初始化人脸数据库
    facefrdata = faceFRData()# 初始化存放人脸识别后返回的数据类:人脸是否存在、检测到的人脸区域、置信度、ID

    def __init__(self, parent=None):
        super(AFRFace, self).__init__(parent)
        self.initARCEngine()
        self.loadFaceFeature()# 加载事先提取好的人脸特征文件pkl

    # 初始化引擎
    def initARCEngine(self):
        # init Engine
        self.pFDWorkMem = CLibrary.malloc(c_size_t(FD_WORKBUF_SIZE))
        self.pFRWorkMem = CLibrary.malloc(c_size_t(FR_WORKBUF_SIZE))

        self.hFDEngine = c_void_p()
        self.ret = AFD_FSDK_InitialFaceEngine(APPID, FD_SDKKEY, self.pFDWorkMem, c_int32(FD_WORKBUF_SIZE),
                                              byref(self.hFDEngine),
                                              AFD_FSDK_OPF_0_HIGHER_EXT, 32, MAX_FACE_NUM)
        # 初始化引擎，若失败则返回该结果
        if self.ret != 0:
            CLibrary.free(self.pFDWorkMem)
            print(u'AFD_FSDK_InitialFaceEngine ret 0x{:x}'.format(self.ret))
            exit(0)

        # print FDEngine version
        versionFD = AFD_FSDK_GetVersion(self.hFDEngine)
        print(u'{} {} {} {}'.format(versionFD.contents.lCodebase, versionFD.contents.lMajor, versionFD.contents.lMinor,
                                    versionFD.contents.lBuild))
        print(c_char_p(versionFD.contents.Version).value.decode(u'utf-8'))
        print(c_char_p(versionFD.contents.BuildDate).value.decode(u'utf-8'))
        print(c_char_p(versionFD.contents.CopyRight).value.decode(u'utf-8'))

        self.hFREngine = c_void_p()
        ret = AFR_FSDK_InitialEngine(APPID, FR_SDKKEY, self.pFRWorkMem, c_int32(FR_WORKBUF_SIZE), byref(self.hFREngine))
        if ret != 0:
            AFD_FSDKLibrary.AFD_FSDK_UninitialFaceEngine(self.hFDEngine)
            CLibrary.free(self.pFDWorkMem)
            CLibrary.free(self.pFRWorkMem)
            print(u'AFR_FSDK_InitialEngine ret 0x{:x}'.format(ret))
            exit(0)

        # print FREngine version 输出人脸比对引擎 版本信息
        versionFR = AFR_FSDK_GetVersion(self.hFREngine)
        print(u'{} {} {} {}'.format(versionFR.contents.lCodebase, versionFR.contents.lMajor, versionFR.contents.lMinor,
                                    versionFR.contents.lBuild))
        print(c_char_p(versionFR.contents.Version).value.decode(u'utf-8'))
        print(c_char_p(versionFR.contents.BuildDate).value.decode(u'utf-8'))
        print(c_char_p(versionFR.contents.CopyRight).value.decode(u'utf-8'))

    def freeEngine(self):

        AFD_FSDK_UninitialFaceEngine(self.hFDEngine)
        AFR_FSDK_UninitialEngine(self.hFREngine)

        CLibrary.free(self.pFDWorkMem)
        CLibrary.free(self.pFRWorkMem)

    def setCam(self, cam):
        self.cam = cam

    def loadFaceFeature(self):
        # 加载人脸特征库
        self.facebase.loadfacedata()

    def addFaceFeature(self, ID, pic_path, name='Unknown', age='Unknown', gender='Unknown'):
        inputImage = loadImageData(pic_path)
        faceFeature = getFeatureFromImg(self.hFDEngine, self.hFREngine, inputImage)# 从图片中提取特征（调用SDK）
        if faceFeature == 0.0:
            print(' get feature from img fail!')
            return

        self.facebase.add_face(faceFeature, ID, name, age, gender)
        self.facebase.savefacedata()

    def setFrameSize(self, width, height):
        # 获取摄像头帧大小
        self.width = width
        self.height = height

    # 获取帧数据
    def inputFrame(self, frame):
        # cv2.imshow('frame', frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # 格式转化
        self.image = GetVideoImage(frame, self.width, self.height)  # opencv 格式 -> SDK可以直接识别的格式

    # 图像格式转化 opencv 格式 -> SDK可以直接识别的格式
    def getImage(self, frame):
        return GetVideoImage(frame, self.width, self.height)

    def getUpdateData(self, updatelists):
        if len(updatelists) > 0:# 如果updatelists不为空，则确实需要更新数据库，令为True
            self.updatefacebase = True
            self.updatelists = updatelists
    '''
    def doUpdate(self):
        while len(self.updatelists) > 0:
            data = self.updatelists.pop()
            if data['option'] == 'add':
                self.addFaceFeature(ID=data['ID'], name=data['name'], pic_path=data['pic_path'])
            elif data['option'] == 'delete':
                self.facebase.removeFaceFeature(ID=data['ID'])
                self.facebase.savefacedata()
                if os.path.exists(data['pic_path']):
                    os.remove(data['pic_path'])
    '''

    # 执行人脸识别
    def run(self):
        image = self.image #opencv从摄像头中用读取到的帧并转化成sdk可识别的格式的image
        face_max_p = 0.0
        face_max_name = 'Unknow'
        face_max_ID = 'Unknow'

        try:
            faces, i = doFaceDetection(self.hFDEngine, image)
            # print('________________________________________________')

            if len(faces) > 0:
                face_exist = True
                # print(face_exist)
                # 获得特征库数据
                faceFeatureBase = self.facebase.getFaceData()
                # 提取人脸的 特征
                featureA = extractFRFeature(self.hFREngine, image, faces[i])
                if featureA == None:
                    print(u'extract face feature in Image faile')
                # 进行人脸比对
                face_max_p, face_max_name, face_max_ID = comparefaces(self.hFREngine, featureA, faceFeatureBase)
            else:
                face_exist = False

            # facefrdata：存放人脸识别后返回的数据类:人脸是否存在、检测到的人脸区域、置信度、ID
            self.facefrdata.setData(face_exist, faces, face_max_p, face_max_name, face_max_ID)      # 数据存放在facefrdata对象中
            # print(face_max_name+'   '+str(face_max_p))
            # 是否太过频繁？更新一次人脸识别就更新一次数据库？
            '''
            if self.updatefacebase:#　如果需要更新数据库的指令为True，则开始更新
                self.doUpdate()# 根据updatelist中的op操作进行增删数据
                self.facebase.loadfacedata()# 更新数据库到pkl中
                self.updatefacebase = False
            '''
        except Exception as e:
            print(e.message)
        finally:
            pass

            # print('__________________________________________________')

class ARCFaceUI(QWidget):
    def __init__(self):
        super(ARCFaceUI, self).__init__()
        self.face_exist = False
        self.face_detected = False

        self.arcface = AFRFace()# 初始化一个线程：初始化引擎、run()用于进行人脸识别
        self.camera = cv2.VideoCapture(0)# 初始化摄像头
        self.detect_face = faceDetect()# 初始化人脸检测类（眨眼检测）,用于判断该帧是否有活体人脸，决定是否保存该帧

        self.arcface.setFrameSize(640, 480)
        self.initUI()  # 初始化界面
        self.startFR()  # 启动读取摄像头线程
        '''
        self.connect_sever = ConnectSever()# 连接到服务器，进行相应的图片同步操作
        '''

        self.through = Through()# 判断置信度，决定是否通过，并记录通过者的信息到list中

        # 定时器
        self.timer = QTimer()
        self.timer.start(20)    # 时间间隔 20ms

        # 线程之间同步操作
        # arcface.finished即当arcface线程的run()函数执行完后，线程则会发出finished信号
        # connect则是完成finished之后触发另一个线程的函数
        self.arcface.finished.connect(self.getResult)  # 当人脸识别线程执行完,执行getresult() 获取结果
        self.connect(self.timer, SIGNAL('timeout()'), self.updateFrame)   # connect连接 定时器timer 每到20ms 就触发更新画面的函数
        '''
        # 与服务器交换数据
        self.connect_sever.finished.connect(self.connect_sever.start)   # 触发服务器与本地数据的同步,ConnectSever类里run一次sleep(60)再执行服务器同步
        self.connect_sever.change.connect(self.arcface.getUpdateData)# 根据change信号(为一个list参数)决定是否需要更新数据到本地
        self.connect_sever.start()# 程序一开始即执行服务器与本地数据同步
        self.through.finished.connect(self.toSever)# through线程判断置信度之后，触发向服务器传图片的toSever函数
        '''

        # 线程之间同步操作
        self.through.pass_sign.connect(self.updateLogo)# 根据pass_sign信号(为一个str参数)决定是否需要更新UI界面上的logo






    def initUI(self):
        self.setWindowTitle(_fromUtf8('AFC FACE'))


        self.exit_button = QtGui.QPushButton(_fromUtf8('退出'))

        self.exit_button.clicked.connect(self.exit_ARC)

        # 摄像机画面的标签
        self.camera_label = QtGui.QLabel(self)
        self.camera_label.setText(_fromUtf8(''))
        self.camera_label.setObjectName('Camera')
        self.camera_label.setScaledContents(True)
        self.camera_label.adjustSize()
        # self.camera_label.setGeometry(0, 0, 800, 600)

        # 检测结果标签
        self.detect_label = QtGui.QLabel(self)
        self.detect_label.setObjectName(_fromUtf8('detect_label'))
        self.detect_label.setText(_fromUtf8('访客姓名:'))
        self.name_text = QtGui.QLineEdit()
        self.name_text.setText(_fromUtf8(' '))

        # 检测 结果的置信度
        self.confidence_label = QtGui.QLabel(self)
        self.confidence_label.setObjectName(_fromUtf8('confidence'))
        self.confidence_label.setText(_fromUtf8('置信度:'))

        self.confid_text = QtGui.QLineEdit()
        self.confid_text.setText(_fromUtf8(' '))

        # 图标标签
        self.icon_label = QtGui.QLabel(self)
        self.logo_png = QtGui.QPixmap('./logo.png')
        self.pass_png = QtGui.QPixmap('./pass.png')
        self.icon_label.setPixmap(self.logo_png)
        self.icon_label.resize(300, 400)

        # self.detect_label.setGeometry(0,400,600,200)



        self.setlayout()
        QtCore.QMetaObject.connectSlotsByName(self)

    def exit_ARC(self):

        self.arcface.facebase.savefacedata()
        self.arcface.exit()
        QCoreApplication.instance().quit()

    def setlayout(self):

        # hbox_button = QHBoxLayout()
        # hbox_button.addStretch(1)
        # hbox_button.addWidget(self.init_face_button)
        # hbox_button.addWidget(self.exit_button)

        # 创建水平布局
        self.hbox = QHBoxLayout()
        self.hbox.addStretch(1)
        self.hbox_left = QHBoxLayout()
        self.hbox_left.addStretch(1)
        self.vbox_right = QVBoxLayout()
        self.vbox_right.addStretch(1)
        # self.vbox_ = QVBoxLayout()
        # self.vbox_.addStretch(1)

        # 创建网格布局
        self.grid_right = QGridLayout()
        self.grid_right.addWidget(self.detect_label, 0, 0)   # 添加姓名标签
        self.grid_right.addWidget(self.name_text, 0, 1)

        self.grid_right.addWidget(self.confidence_label, 1, 0)   # 置信度标签
        self.grid_right.addWidget(self.confid_text, 1, 1)

        # self.grid_right.addWidget(self.exit_button, 8, 0)

        self.hbox_left.addWidget(self.camera_label)   #  摄像头画面标签
        self.vbox_right.addWidget(self.icon_label)
        self.vbox_right.addLayout(self.grid_right)
        self.vbox_right.addWidget(self.exit_button)

        # self.hbox_left.setScaledContents()

        self.hbox.addLayout(self.hbox_left)
        self.hbox.addLayout(self.vbox_right)

        # self.vbox_.addLayout(self.hbox)

        # 应用布局
        self.setLayout(self.hbox)

    def updateFacebase(self):
        self.arcface.updatefacebase = True

    # 开始读取摄像头线程
    def startFR(self):
        ret, frame = self.camera.read()# 从摄像头中读取帧
        self.arcface.inputFrame(frame)# 用opencv的帧初始化，并将其转换成SDK可直接识别的图片格式
        # if self.face_detected:
        self.arcface.start()# 启动该线程

    # 获得结果
    def getResult(self):
        self.result = self.arcface.facefrdata# 人脸识别后返回的数据结果
        self.updateResult()# 将识别结果更新到GUI上
        # print(self.result.faceName)
        if self.face_exist:
            self.passThrough()# 调用Through类的run()对置信度比较阈值，决定是否通过
        # else:
        #     self.updateLogo('can not pass')
        # self.startFR() #再获取一帧

    # 将人脸的置信度和名字 更新到GUI上
    def updateResult(self):
        p = self.result.p # 置信度
        faceName = self.result.faceName #识别到的人脸的名字

        self.confid_text.setText(_fromUtf8(str(p)))
        self.name_text.setText(_fromUtf8(faceName))

    # 第一次调用Through类时，要在这里启动through类的run()
    def passThrough(self):
        self.updateLogo() #如果不需要向服务器传数据就要在这决定是否更新logo
        self.through.inputFRResult(self.result, self.face_exist)# 将人脸识别的结果赋值给QThread类
        self.through.start()# 第一次启动继承QThread的through类该线程 ，用于进行置信度比对，决定是否通过

    def updateLogo(self, passthrough=''):# passthrough为接收的信号
        if passthrough == 'PASS':
            # jpg = QtGui.QPixmap('./pass.png')
            self.icon_label.setPixmap(self.pass_png)
        else:
            self.icon_label.setPixmap(self.logo_png)

        self.icon_label.resize(300, 400)

    '''
    # 把通过的识别到的人脸图片上传到服务器
    def toSever(self):
        self.updateLogo()#如果人脸通过，则更换logo图标
        if len(self.through.through_lists) > 0:
            self.connect_sever.inputUploadData(self.through.through_lists.pop())
    '''


    # 格式转化
    def fromFrame2QImage(self, frame):
        height, width, bytesPerComponent = frame.shape
        bytesPerLine = bytesPerComponent * width
        # 变换彩色空间顺序
        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB, frame)
        # 转为QImage对象
        image = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
        return image

    # 更新摄像头画面
    def updateFrame(self):
        ret, frame = self.camera.read()
        frame_output, face_detected, face_exist = self.detect_face.detectFace(frame)
        self.face_exist = face_exist
        self.face_detected = face_detected
        if not self.arcface.isRunning():
            self.startFR()

        frame_Qimage = self.fromFrame2QImage(frame_output)
        self.camera_label.setPixmap(QtGui.QPixmap.fromImage(frame_Qimage))


def main():
    app = QtGui.QApplication(sys.argv)# 初始化QtGui
    window = ARCFaceUI()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()