import dlib
import os
import cv2
import numpy as np
# from AFR_test_use_min_image import *
from my_untils import *
import pickle

predictor_path = "./shape_predictor_68_face_landmarks.dat"
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

'''
def getOrient(face_input='facedata/faces', face_output='facedata/smallimg/'):
    # init Engine
    pFDWorkMem = CLibrary.malloc(c_size_t(FD_WORKBUF_SIZE))
    pFRWorkMem = CLibrary.malloc(c_size_t(FR_WORKBUF_SIZE))

    hFDEngine = c_void_p()
    ret = AFD_FSDK_InitialFaceEngine(APPID, FD_SDKKEY, pFDWorkMem, c_int32(FD_WORKBUF_SIZE), byref(hFDEngine),
                                     AFD_FSDK_OPF_0_HIGHER_EXT, 32, MAX_FACE_NUM)
    if ret != 0:
        CLibrary.free(pFDWorkMem)
        print(u'AFD_FSDK_InitialFaceEngine ret 0x{:x}'.format(ret))
        exit(0)

    # print FDEngine version
    versionFD = AFD_FSDK_GetVersion(hFDEngine)
    print(u'{} {} {} {}'.format(versionFD.contents.lCodebase, versionFD.contents.lMajor, versionFD.contents.lMinor,
                                versionFD.contents.lBuild))
    print(c_char_p(versionFD.contents.Version).value.decode(u'utf-8'))
    print(c_char_p(versionFD.contents.BuildDate).value.decode(u'utf-8'))
    print(c_char_p(versionFD.contents.CopyRight).value.decode(u'utf-8'))

    hFREngine = c_void_p()
    ret = AFR_FSDK_InitialEngine(APPID, FR_SDKKEY, pFRWorkMem, c_int32(FR_WORKBUF_SIZE), byref(hFREngine))
    if ret != 0:
        AFD_FSDKLibrary.AFD_FSDK_UninitialFaceEngine(hFDEngine)
        CLibrary.free(pFDWorkMem)
        CLibrary.free(pFRWorkMem)
        print(u'AFR_FSDK_InitialEngine ret 0x{:x}'.format(ret))
        System.exit(0)

    # print FREngine version
    versionFR = AFR_FSDK_GetVersion(hFREngine)
    print(u'{} {} {} {}'.format(versionFR.contents.lCodebase, versionFR.contents.lMajor, versionFR.contents.lMinor,
                                versionFR.contents.lBuild))
    print(c_char_p(versionFR.contents.Version).value.decode(u'utf-8'))
    print(c_char_p(versionFR.contents.BuildDate).value.decode(u'utf-8'))
    print(c_char_p(versionFR.contents.CopyRight).value.decode(u'utf-8'))

    # face_detect = 'face_detect'


    o = {}

    list_face_base = os.listdir(face_input)
    # list_face_detect = os.listdir(face_detect)

    for file in list_face_base:
        filePathTemp = os.path.join(face_input, file)
        input_img = loadImageData(filePathTemp)
        print (file)
        faceInfos, i = doFaceDetection(hFDEngine, input_img)
        if len(faceInfos) < 1:
            print(u'no face in Image')
            continue

        o[file] = {'left': faceInfos[i].left, 'top': faceInfos[i].top, 'right': faceInfos[i].right,
                   'bottom': faceInfos[i].bottom, 'orient': faceInfos[i].orient}

    if not os.path.exists(face_output):
        os.mkdir(face_output)
    with open(os.path.join(face_output, 'orient.pkl'), 'wb') as f:

        pickle.dump(o, f, 0)
    print(o)
'''


if __name__ == u'__main__':
    getSmallImg()
    # getOrient()
