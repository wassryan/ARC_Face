# -*- encoding=utf-8 -*-
from arcsoft import AFD_FSDKLibrary
# from Connect_Sever import *
from my_untils.throughDoor import *
from my_untils.search_compare import *
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *
from PyQt4.QtCore import *
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

class ARCFaceUI(QWidget):
    def __init__(self):
        super(ARCFaceUI, self).__init__()
        self.true_face = False
        self.face_detected = False

        self.arcface = FRFace()# 初始化一个线程：初始化引擎、run()用于进行人脸识别
        self.detect_face = FDFace()# 初始化人脸检测类（眨眼检测）,用于判断该帧是否有活体人脸，决定是否保存该帧
        self.camera = cv2.VideoCapture(0)# 初始化摄像头

        self.arcface.setFrameSize(640, 480)
        self.initUI()  # 初始化界面
        self.through = Through()# 判断置信度，决定是否通过，并记录通过者的信息到list中

        # 定时器
        self.timer = QTimer()
        self.timer.start(20)    # 时间间隔 20ms

        # 线程之间同步操作
        # arcface.finished即当arcface线程的run()函数执行完后，线程则会发出finished信号
        # connect则是完成finished之后触发另一个线程的函数
        self.arcface.finished.connect(self.getResult)  # 当人脸识别线程执行完,执行getresult() 获取结果
        self.connect(self.timer, SIGNAL('timeout()'), self.updateFrame)   # connect连接 定时器timer 每到20ms 就触发更新画面的函数
        self.through.pass_sign.connect(self.updateLogo)# 根据pass_sign信号(为一个str参数)决定是否需要更新UI界面上的logo

        '''
        # 与服务器交换数据
        self.connect_sever = ConnectSever()# 连接到服务器，进行相应的图片同步操作
        self.connect_sever.finished.connect(self.connect_sever.start)   # 触发服务器与本地数据的同步,ConnectSever类里run一次sleep(60)再执行服务器同步
        self.connect_sever.change.connect(self.arcface.getUpdateData)# 根据change信号(为一个list参数)决定是否需要更新数据到本地
        self.connect_sever.start()# 程序一开始即执行服务器与本地数据同步
        self.through.finished.connect(self.toSever)# through线程判断置信度之后，触发向服务器传图片的toSever函数
        '''

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

    # 读取帧画面，启动人脸识别线程
    def startFR(self):
        ret, frame = self.camera.read()# 从摄像头中读取帧
        self.arcface.inputFrame(frame)# 转换成SDK可直接识别的图片格式
        self.arcface.start()# 启动该线程

    # 获得结果
    def getResult(self):
        self.result = self.arcface.facefrdata# 人脸识别后返回的数据结果
        self.updateResult()# 将识别结果更新到GUI上
        # print(self.result.faceName)
        if self.true_face:
            self.passThrough()# 调用Through类的run()对置信度比较阈值，决定是否通过
        # else:
        #     self.updateLogo('can not pass')
        # self.ReadCamera() #再获取一帧

    # 将人脸的置信度和名字 更新到GUI上
    def updateResult(self):
        p = self.result.p # 置信度
        faceName = self.result.faceName #识别到的人脸的名字
        self.confid_text.setText(_fromUtf8(str(p)))
        self.name_text.setText(_fromUtf8(faceName))

    # 第一次调用Through类时，要在这里启动through类的run()
    def passThrough(self):
        self.through.inputFRResult(self.result, self.true_face)# 将人脸识别的结果赋值给QThread类
        self.through.start()# 第一次启动继承QThread的through类该线程 ，用于进行置信度比对，决定是否通过

    def updateLogo(self, passthrough=''):# 由pass_sign信号触发该槽函数（带一个参数的槽函数）
        if passthrough == 'PASS':
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
        frame_output, face_detected, true_face = self.detect_face.detectFace(frame)
        self.true_face = true_face
        self.face_detected = face_detected
        if self.true_face: # 是真的人脸 才运行人脸识别
            self.startFR()
        else:
            p = 0
            faceName = 'Unknown'
            self.confid_text.setText(_fromUtf8(str(p)))
            self.name_text.setText(_fromUtf8(faceName))
            self.updateLogo(passthrough='')

        frame_Qimage = self.fromFrame2QImage(frame_output)
        self.camera_label.setPixmap(QtGui.QPixmap.fromImage(frame_Qimage))

def main():
    app = QtGui.QApplication(sys.argv)# 初始化QtGui
    window = ARCFaceUI()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()