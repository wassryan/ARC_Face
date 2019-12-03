# -*- encoding=utf-8 -*-
import dlib
import os
import cv2
import numpy as np
from AFR_face import *
import pickle

predictor_path = "/home/kary/Projects/ARC Face Project/shape_predictor_68_face_landmarks.dat"
detect = dlib.get_frontal_face_detector()

predictor = dlib.shape_predictor(predictor_path)
rescale = [1.185974, 1.0, 1.135600, 1.17]


def cropImg(img, tlx, tly, brx, bry, rescale):
    l = float(tlx)
    t = float(tly)
    ww = float(brx - l)
    hh = float(bry - t)

    # Approximate LM tight BB
    h = img.shape[0]
    w = img.shape[1]
    # cv2.rectangle(img, (int(l), int(t)), (int(brx), int(bry)), \
    #     (0, 255, 255), 2)
    cx = l + ww / 2
    cy = t + hh / 2
    tsize = max(ww, hh) / 2
    l = cx - tsize
    t = cy - tsize

    # Approximate expanded bounding box
    bl = int(round(cx - rescale[0] * tsize))
    bt = int(round(cy - rescale[1] * tsize))
    br = int(round(cx + rescale[2] * tsize))
    bb = int(round(cy + rescale[3] * tsize))
    nw = int(br - bl)
    nh = int(bb - bt)
    imcrop = np.zeros((nh, nw, 3), dtype='uint8')

    ll = 0
    if bl < 0:
        ll = -bl
        bl = 0
    rr = nw
    if br > w:
        rr = w + nw - br
        br = w
    tt = 0
    if bt < 0:
        tt = -bt
        bt = 0
    bbb = nh
    if bb > h:
        bbb = h + nh - bb
        bb = h
    imcrop[tt:bbb, ll:rr, :] = img[bt:bb, bl:br, :]
    return imcrop

# 选取最大的人脸
def getMaxface(dets, scores, idx, minconfid=0.6):
    # maxsizeface = dets[0]
    maxsize = 0.0
    maxi = 0
    for i, d in enumerate(dets):
        if scores[i] < minconfid:
            print(u' the face {} in image not very clearly '.format(i))
            continue
        size = (d.right() - d.left()) * (d.bottom() - d.top())
        if maxsize < size:
            maxsize = size
            maxi = i

    return dets[maxi], maxi


def getSmallImg(input_dir='face_base/', output_path='facedata/faces/'):
    # input_dir = 'face_base_10/'
    filelists = os.listdir(input_dir)
    # print(filelists)
    # o = {}

    for file in filelists:
        print(file)
        img = cv2.imread(input_dir + file)

        dets, scores, idx = detect.run(img, 1, -1)

        det_face = dets[0]
        i = 0

        if len(dets) == 0:
            print('the image fail to detect face!')
            continue
        if len(dets) > 1:
            print('we only use one face in an image')
            det_face, i = getMaxface(dets, scores, idx, minconfid=0.6)

        # for i, det_face in enumerate(dets):

        print('Dec:{},confidence:{}'.format(i, scores[i]))
        imgcrop = cropImg(img, det_face.left(), det_face.top(), det_face.right(), det_face.bottom(), rescale)

        if not os.path.exists(output_path):
            os.mkdir(output_path)

        cv2.imwrite(os.path.join(output_path, file), imgcrop)