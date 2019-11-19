from PyQt4 import QtCore, QtGui
from PyQt4.phonon import *
import sys

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    videofrom = QtGui.QWidget()
    videofrom.setWindowTitle('Video Player')
    videofrom.resize(400,400)
    media = Phonon.MediaObject()
    media.setCurrentSource(Phonon.MediaSource('../cn.avi'))

    vwidget = Phonon.VideoWidget(videofrom)
    Phonon.createPath(media, vwidget)

    vwidget.setAspectRatio(Phonon.VideoWidget.AspectRatioAuto)
    aOutput = Phonon.AudioOutput(Phonon.VideoCategory)
    Phonon.createPath(media, aOutput)

    labe = QtGui.QLabel('Volume:')
    volumeSlider = Phonon.VolumeSlider()
    volumeSlider.setAudioOutput(aOutput)
    volumeSlider.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)

    seekSlider = Phonon.SeekSlider()
    seekSlider.setMediaObject(media)

    hLayout = QtGui.QHBoxLayout()
    hLayout.addWidget(labe)
    hLayout.addWidget(volumeSlider)
    hLayout.addStretch()

    vLayout = QtGui.QVBoxLayout()
    vLayout.addWidget(vwidget)
    vLayout.addWidget(seekSlider)
    vLayout.addLayout(hLayout)
    videofrom.setLayout(vLayout)

    videofrom.show()
    media.play()

    sys.exit(app.exec_())