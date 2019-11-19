# -*- coding: utf-8 -*-

import cv2
import numpy as np
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import phonon
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

class UI_Window(QtGui.QWidget):

    def __init__(self):
        super(UI_Window,self).__init__()

    def initUI(self, Window):
        Window.setObjectName(_fromUtf8('AFC FACE'))
        Window.resize(800, 600)
        self.init_face_button = QtGui.QPushButton(Window)
        self.init_face_button.setObjectName(_fromUtf8('注册'))

        self.exit_button = QtGui.QPushButton(Window)
        self.exit_button.setObjectName(_fromUtf8('退出'))

        self.camera_label = QtGui.QLabel(Window)
        self.camera_label.setText(_fromUtf8(''))
        self.camera_label.setObjectName('Camera')

        self.detect_labe = QtGui.QLabel(Window)
        self.detect_labe.setObjectName(_fromUtf8('detect_label'))

        # self.setlayout()
        QtCore.QMetaObject.connectSlotsByName(Window)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("ARC", "Face", None))
        self.init_face_button.setText(_translate("Dialog", "注册", None))
        self.exit_button.setText(_translate("Dialog", "退出", None))
        self.camera_label.setText(_translate("Dialog", "视频", None))
        self.detect_labe.setText(_translate("Dialog", "识别结果", None))

        self.hbox = QHBoxLayout()
        self.hbox_media = QHBoxLayout()
    def setlayout(self):

        # 水平布局

        self.hbox.addStretch(1)
        self.hbox.addWidget(self.init_face_button)
        self.hbox.addWidget(self.exit_button)


        self.hbox_media.addStretch(1)
        self.hbox_media.addWidget(self.camera_label)

        # 垂直布局

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addWidget(self.hbox)
        # vbox.addWidget(self.hbox_media)

        self.setLayout(vbox)


class CameraDevice(QtGui.QDialog):

    def __init__(self, cameraId=0, mirrored=False):
        super(CameraDevice, self).__init__()
        self.mirrored = mirrored
        self.cam = self.openCamera()
        # self.frame = self.getFrame()
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.getFrame)

        self.paused = False
    def openCamera(self, cameraID=0):
        global timer
        timer.start(20)
        return cv2.VideoCapture(cameraID)

    @QtCore.pyqtSlot()
    def getFrame(self):
        ret, frame = self.cam.read()
        return frame

    def getFrameSize(self,frame):
        h, w = self.cam.get(cv2.CAP_PROP_FRAME_HEIGHT), self.cam.get(cv2.CAP_PROP_FRAME_WIDTH)
        return int(h), int(w)

    def frameCvtBGR2RGB(self, frame):
        frameRGB = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        return frameRGB

    def frameFlip(self, frame):
        return cv2.flip(frame, 1)

    def fromFrame2QImage(self,frame):
        height, width, bytesPerComponent = frame.shape
        bytesPerLine = bytesPerComponent * width
        # 变换彩色空间顺序
        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB, frame)
        # 转为QImage对象
        self.image = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
        return self.image

class Window(QWidget):
    def __init__(self):
        global timer
        timer = QTimer()
        super(Window, self).__init__()
        # self.ui = UI_Window()
        self.initUI()
        self.cam = CameraDevice()

        self.connect(timer, SIGNAL("timeout()"), self.updateFrame)
        self.updateFrame()

    def initUI(self):
        self.setObjectName(_fromUtf8('AFC FACE'))
        # self.resize(800, 600)
        self.init_face_button = QtGui.QPushButton(_fromUtf8('注册人脸'))
        self.init_face_button.setGeometry(0, 800, 40, 20)
        # self.init_face_button.setObjectName()

        self.exit_button = QtGui.QPushButton(_fromUtf8('退出'))

        self.exit_button.clicked.connect(QCoreApplication.instance().quit)

        self.camera_label = QtGui.QLabel(self)
        self.camera_label.setText(_fromUtf8(''))
        self.camera_label.setObjectName('Camera')
        # self.camera_label.setGeometry(0, 0, 800, 600)

        self.detect_label = QtGui.QLabel(self)
        self.detect_label.setObjectName(_fromUtf8('detect_label'))
        self.detect_label.setText(_fromUtf8('访客姓名:'))
        self.name_text = QtGui.QLineEdit()
        self.name_text.setText(_fromUtf8(' '))

        self.confidence_label = QtGui.QLabel(self)
        self.confidence_label.setObjectName(_fromUtf8('confidence'))
        self.confidence_label.setText(_fromUtf8('置信度:'))

        self.confid_text = QtGui.QLineEdit()
        self.confid_text.setText(_fromUtf8(' '))

        # self.detect_label.setGeometry(0,400,600,200)



        self.setlayout()
        QtCore.QMetaObject.connectSlotsByName(self)

    def setlayout(self):

        hbox_button = QHBoxLayout()
        hbox_button.addStretch(1)
        hbox_button.addWidget(self.init_face_button)
        hbox_button.addWidget(self.exit_button)

        self.hbox = QHBoxLayout()
        self.hbox.addStretch(1)
        self.hbox_left = QHBoxLayout()
        self.hbox_left.addStretch(1)
        self.vbox_right = QVBoxLayout()
        self.vbox_right.addStretch(1)

        self.grid_right = QGridLayout()



        self.grid_right.addWidget(self.detect_label, 0, 0)
        self.grid_right.addWidget(self.name_text, 0, 1)

        self.grid_right.addWidget(self.confidence_label, 1, 0)
        self.grid_right.addWidget(self.confid_text, 1, 1)

        # self.grid_right.addWidget(self.exit_button, 8, 0)



        self.hbox_left.addWidget(self.camera_label)
        self.vbox_right.addLayout(self.grid_right)
        self.vbox_right.addWidget(self.exit_button)
        self.hbox.addLayout(self.hbox_left)
        self.hbox.addLayout(self.vbox_right)



        self.setLayout(self.hbox)

    def updateFrame(self):
        frame = self.cam.getFrame()
        frame_Qimage = self.cam.fromFrame2QImage(frame)
        self.camera_label.setPixmap(QtGui.QPixmap.fromImage(frame_Qimage))

    def getFrame(self):
        return self.cam.getFrame()

    def updateResult(self, confidence = 0.0, name = ' '):
        self.confid_text.setText(_fromUtf8(confidence))
        self.name_text.setText(_fromUtf8(name))

    def drawEvent(self, x, y, w, h):
        qp = QtGui.QPainter()
        qp.begin(self.hbox_left)
        self.drawRectangles(qp, x, y, w, h)
        qp.end()


    def drawRectangles(self, qp, x, y, w, h):
        # 设置颜色
        color = QtGui.QColor(200, 0, 0)
        qp.setPen(color)
        qp.drawRect(x, y, w, h)




def main():
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
