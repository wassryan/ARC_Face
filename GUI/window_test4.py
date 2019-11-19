#-*- encoding=utf-8 -*-

import sys
import time
from PyQt4 import QtCore, QtGui
from PyQt4 import phonon
from PyQt4.QtCore import *
from PyQt4.QtGui import *

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

import cv2
import numpy as np

class CameraDevice(QtGui.QDialog):

    def __init__(self, cameraId=0, mirrored=False):
        super(CameraDevice, self).__init__()
        self.mirrored = mirrored
        self.cam = cv2.VideoCapture(cameraId)
        self.frame = self.getFrame()
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.getFrame)

        self.paused = False

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


class Timer(QtCore.QThread):
    def __init__(self, signal="updateTime()", parent=None):
        super(Timer, self).__init__(parent)
        self.stoped = False
        self.signal = signal
        self.mutex = QtCore.QMutex()

    def run(self):
        with QtCore.QMutexLocker(self.mutex):
            self.stoped = False
        while True:
            if self.stoped:
                return
            self.emit(QtCore.SIGNAL(self.signal))
            time.sleep(0.04)

    def stop(self):
        with QtCore.QMutexLocker(self.mutex):
            self.stoped = True

    def isStoped(self):
        with QtCore.QMutexLocker(self.mutex):
            return self.stoped


class WindowMain(QWidget):
    model = None

    def __init__(self):
        super(WindowMain, self).__init__()
        self.initUI()
        self.image = QImage()
        self.camera = cv2.VideoCapture(0)
        self.playTimer = Timer('updatePlay()')
        self.connect(self.playTimer, SIGNAL('updatePlay()'), self.showCamer)


    def initUI(self):
        # self.media = phonon.Phonon.MediaObject()
        # # self.media.setCurrentSource(phonon.Phonon.MediaSource())
        #
        # vwidget = phonon.Phonon.VideoWidget(self)
        # phonon.Phonon.createPath(self.media, vwidget)

        # camera = CameraDevice(0)
        # camerawidget = CameraWidget(camera)
        # camerawidget.paintEvent()

        # 注册按钮
        button_init = QPushButton(_fromUtf8('注册人脸'), self)
        button_init.setToolTip(_fromUtf8('在人脸特征数据库中添加特征信息'))
        # button_init.resize(button_init.sizeHiint())
        # button.move(20,700)

        # 退出按钮
        button_quit = QPushButton(_fromUtf8('Quit'), self)
        # button_quit.connectNotify(QCoreApplication.instance().quit())
        button_quit.clicked.connect(QCoreApplication.instance().quit)
        # button_quit.resize(button_quit.sizeHint())
        # button_quit.move(280,700)

        hbox_media = QHBoxLayout()
        hbox_media.addStretch(1)
        # hbox_media.addWidget(camerawidget)

        # 水平布局
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(button_init)
        hbox.addWidget(button_quit)

        # 垂直布局
        vbox = QVBoxLayout()
        vbox.addStretch(1)
        # 将水平布局放入垂直布局中
        vbox.addLayout(hbox)
        vbox.addLayout(hbox_media)

        self.setLayout(vbox)

        self.setGeometry(300, 300, 480, 800)
        self.setWindowTitle('ARC_face')
        # self.setWindowIcon(QIcon('web.png'))

        self.show()

    def showCamer(self):
        if self.camera.isOpened():
            ret, frame = self.camera.read()
        else:
            ret = False
        height, width, bytesPerComponent = frame.shape
        bytesPerLine = bytesPerComponent * width
        # 变换彩色空间顺序
        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB, frame)
        # 转为QImage对象
        self.image = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
        self.setPixmap(QPixmap.fromImage(self.image))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    windows = WindowMain()
    windows.playTimer.start()
    windows.show()
    sys.exit(app.exec_())


