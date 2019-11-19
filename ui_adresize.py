# -*- encoding=utf-8 -*-

from FaceBase import *
from AFR_face import *
from arcsoft import AFD_FSDKLibrary
from Connect_Sever import *
from my_untils.throughDoor import *
import sys
import cv2
import numpy as np
from time import sleep
import dlib
from imutils import face_utils
from my_untils.eye_blink import *
# from my_untils.search_compare import *
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


# APPID = c_char_p(b'8HFRpRpZkfryTmatRE9nPoDmFMvtTZrPNUWYiw4NX632')
# FD_SDKKEY = c_char_p(b'EZTSC8o99X9Hh999tVNP1xsyYnADcDniL1PznE3rUSoB')
# FR_SDKKEY = c_char_p(b'EZTSC8o99X9Hh999tVNP1xtUCPCtzN3bWVbQ6PZaq8jB')
APPID = c_char_p(b'FBmQrBiFKgDS4UenPAXXSmH4mWXSd6V5oq4yFc17YynT')
FD_SDKKEY = c_char_p(b'C4wd8EyQjD57EPbXuPmSBLjxwJpRMJPb66HjuwWitHE7')
FR_SDKKEY = c_char_p(b'C4wd8EyQjD57EPbXuPmSBLkTaus8JFvgpQRxuvRHQcC3')
FD_WORKBUF_SIZE = 20 * 1024 * 1024
FR_WORKBUF_SIZE = 40 * 1024 * 1024
MAX_FACE_NUM = 50
bUseYUVFile = False
bUseBGRToEngine = True


class AFRFace(QThread):
    updatefacebase = False
    updatelists = []
    facebase = FaceBase()
    facefrdata = faceFRData()

    def __init__(self, parent=None):
        super(AFRFace, self).__init__(parent)
        # self.facefrdata = faceFRData()
        # self.facebase = FaceBase()
        self.initARCEngine()
        self.loadFaceFeature()

    # 初始化引擎
    def initARCEngine(self):
        # init Engine
        self.pFDWorkMem = CLibrary.malloc(c_size_t(FD_WORKBUF_SIZE))
        self.pFRWorkMem = CLibrary.malloc(c_size_t(FR_WORKBUF_SIZE))

        self.hFDEngine = c_void_p()
        self.ret = AFD_FSDK_InitialFaceEngine(APPID, FD_SDKKEY, self.pFDWorkMem, c_int32(FD_WORKBUF_SIZE),
                                              byref(self.hFDEngine),
                                              AFD_FSDK_OPF_0_HIGHER_EXT, 32, MAX_FACE_NUM)
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
        faceFeature = getFeatureFromImg(self.hFDEngine, self.hFREngine, inputImage)
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
        if len(updatelists) > 0:
            self.updatefacebase = True
            self.updatelists = updatelists

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

    # 执行人脸识别
    def run(self):
        image = self.image
        face_max_p = 0.0
        face_max_name = 'Unknow'
        face_max_ID = 'Unknow'

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

        self.facefrdata.setData(face_exist, faces, face_max_p, face_max_name, face_max_ID)      # 数据存放在facefrdata对象中
        # print(face_max_name+'   '+str(face_max_p))
        if self.updatefacebase:
            self.doUpdate()
            self.facebase.loadfacedata()
            self.updatefacebase = False

class ARCFaceUI(QWidget):
    def __init__(self):
        super(ARCFaceUI, self).__init__()
        self.face_exist = False
        self.face_detected = False

        self.arcface = AFRFace()
        self.camera = cv2.VideoCapture(0)
        self.detect_face = faceDetect()

        self.arcface.setFrameSize(640, 480)
        self.initUI()  # 初始化界面
        self.startFR()  # 启动人脸识别线程

        self.connect_sever = ConnectSever()
        # self.connect_sever.setArcface(self.arcface)

        self.through = Through()

        # 定时器
        self.timer = QTimer()
        self.timer.start(20)    # 时间间隔 20ms

        # self.timer_sever = QTimer()
        # self.timer_sever.start(3000)

        self.arcface.finished.connect(self.getResult)  # 当人脸检测线程执行完,执行getresult() 获取结果
        self.connect(self.timer, SIGNAL('timeout()'), self.updateFrame)   # 定时器timer 没到20ms 更新画面
        self.connect_sever.finished.connect(self.connect_sever.start)
        self.through.finished.connect(self.toSever)
        self.connect_sever.change.connect(self.arcface.getUpdateData)

        self.connect_sever.start()



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
        jpg = QtGui.QPixmap('./face_1.png')
        self.icon_label.setPixmap(jpg)
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
        self.hbox.addStretch()
        self.vbox = QVBoxLayout()
        self.vbox.addStretch()
        self.hbox_left = QHBoxLayout()
        self.hbox_left.addStretch()
        self.vbox_right = QVBoxLayout()
        self.vbox_right.addStretch()

        self.grid_center = QGridLayout()


        # 创建网格布局
        self.grid_right = QGridLayout()
        self.grid_right.addWidget(self.detect_label, 0, 0)   # 添加姓名标签
        self.grid_right.addWidget(self.name_text, 0, 1)

        self.grid_right.addWidget(self.confidence_label, 1, 0)   # 置信度标签
        self.grid_right.addWidget(self.confid_text, 1, 1)

        # self.grid_right.addWidget(self.exit_button, 8, 0)

        self.vbox.addWidget(self.camera_label)   #  摄像头画面标签
        # self.grid_center.addLayout(self.vbox, 0, 0)
        self.vbox_right.addWidget(self.icon_label)
        self.vbox_right.addLayout(self.grid_right)
        self.vbox_right.addWidget(self.exit_button)

        # self.grid_center.addLayout(self.vbox_right, 0, 1)

        self.hbox.addLayout(self.vbox)
        self.hbox.addLayout(self.vbox_right)
        #
        # self.vbox.addLayout(self.hbox)

        # 应用布局
        self.setLayout(self.hbox)

    def updateFacebase(self):
        self.arcface.updatefacebase = True

    # 开始人脸识别线程
    def startFR(self):
        ret, frame = self.camera.read()
        self.arcface.inputFrame(frame)
        # if self.face_detected:
        self.arcface.start()

    # 获得结果
    def getResult(self):
        self.result = self.arcface.facefrdata
        self.updateResult()
        # print(self.result.faceName)
        if self.face_exist:
            self.passThrough()
        self.startFR()

    # 将检测结果更新到GUI上
    def updateResult(self):
        p = self.result.p
        faceName = self.result.faceName

        self.confid_text.setText(_fromUtf8(str(p)))
        self.name_text.setText(_fromUtf8(faceName))

    def passThrough(self):
        self.through.inputFRResult(self.result, self.face_exist)
        self.through.start()

    def toSever(self):
        if len(self.through.through_lists) > 0:
            self.connect_sever.inputUploadData(self.through.through_lists.pop())


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
    app = QtGui.QApplication(sys.argv)
    window = ARCFaceUI()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()