# -*- encoding=utf-8 -*-

from arcsoft import CLibrary, ASVL_COLOR_FORMAT, ASVLOFFSCREEN, c_ubyte_p, FaceInfo,AFD_FSDKLibrary,AFR_FSDKLibrary
# from utils import BufferInfo, ImageLoader
# from ..arcsoft.AFD_FSDKLibrary import *
# from ..arcsoft.AFR_FSDKLibrary import *
from ctypes import *
from FaceBase import *
import traceback
import os
import time
from AFR_face import *

APPID = c_char_p(b'FBmQrBiFKgDS4UenPAXXSmH4mWXSd6V5oq4yFc17YynT')
FD_SDKKEY = c_char_p(b'C4wd8EyQjD57EPbXuPmSBLjxwJpRMJPb66HjuwWitHE7')
FR_SDKKEY = c_char_p(b'C4wd8EyQjD57EPbXuPmSBLkTaus8JFvgpQRxuvRHQcC3')
FD_WORKBUF_SIZE = 20 * 1024 * 1024
FR_WORKBUF_SIZE = 40 * 1024 * 1024
MAX_FACE_NUM = 50
bUseYUVFile = False
bUseBGRToEngine = True

def loadImageData(path):
    # load Image Data
    if bUseYUVFile:# False
        filePathA = path
        yuv_widthA = 640
        yuv_heightA = 480
        yuv_formatA = ASVL_COLOR_FORMAT.ASVL_PAF_I420

        return loadYUVImage(filePathA, yuv_widthA, yuv_heightA, yuv_formatA)

    else:
        filePath = path
        return loadImage(filePath)

def serach_compare(img_name,faces):

    start = time.time()
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


    hFREngine = c_void_p()
    ret = AFR_FSDK_InitialEngine(APPID, FR_SDKKEY, pFRWorkMem, c_int32(FR_WORKBUF_SIZE), byref(hFREngine))
    if ret != 0:
        AFD_FSDKLibrary.AFD_FSDK_UninitialFaceEngine(hFDEngine)
        CLibrary.free(pFDWorkMem)
        CLibrary.free(pFRWorkMem)
        print(u'AFR_FSDK_InitialEngine ret 0x{:x}'.format(ret))
        sys.exit(0)
    end =time.time()
    print(u'Init Egine use time {0} s'.format(end - start))# 0.006s

    dataset = 'facedata/faces/'
    face_in = 'face_detect/'

    # start = time.time()
    # face = FaceBase()
    # face.loadfacedata()# 载入人脸特征pkl文件，移步至demo.py文件处
    # end =time.time()
    # print(u'Loading pkl use time {0} s'.format(end - start))# 0.45s
    # print type(face.faces)

    # 加载待识别的人脸照片
    start = time.time()
    print "Processing {0}".format(img_name)
    filePathA = face_in + '/' + img_name
    inputImageA = loadImageData(filePathA)
    # 提取待检测的图片的人脸特征(最大人脸框的人脸)
    featureA = getFeatureFromImg(hFDEngine=hFDEngine, hFREngine=hFREngine, inputImg=inputImageA)

    if featureA == 0.0:# 如果摄像头获取的人脸无法提取特征，则pass掉后面的部分
        print('extractFRFeature fail.')
        return 'Uknown',0

    face_max_p = 0.0
    face_max_name = 'Unknown'
    face_max_ID = 'Unknown'


    # 人脸特征匹配
    # 从存放人脸特征的字典中获取所有图片的人脸信息(字典)
    for k, v in faces.getFaceData():
        featureB = v['FaceFeature']
        if featureB == 0.0:
            print('extractFRFeature fail.You need to check the *.pkl file')
            continue
        # 返回人脸的相似度，并释放了featureB的内存
        p = compareFeatureSimilarytey(hFREngine, featureA, featureB)
        # print('{0}: {1}'.format(k, p.value))

        # 找到最大的人脸特征对应的Name
        pj = p.value
        if pj > face_max_p:
            face_max_p = p.value
            face_max_name = v['Name']

    print('max_p {0}'.format(face_max_p))
    if face_max_p < 0.5:
        face_max_name = 'Unknown'
        face_max_p = 0.0
    end = time.time()
    print(u'Compare Feature use time {0} s'.format(end - start))# 0.2
    # print(u'It is {0}'.format(face_max_name))
    print(u'Similarity score is:{0}'.format(face_max_p))
    featureA.freeUnmanaged()

    # release Engine
    AFD_FSDK_UninitialFaceEngine(hFDEngine)
    AFR_FSDK_UninitialEngine(hFREngine)

    CLibrary.free(pFDWorkMem)
    CLibrary.free(pFRWorkMem)
    print('________________________________________________________________________')
    return face_max_name,face_max_p

'''
if __name__ == u'__main__':
    print(u'#####################################################')

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
    # versionFD = AFD_FSDK_GetVersion(hFDEngine)
    # print(u'{} {} {} {}'.format(versionFD.contents.lCodebase, versionFD.contents.lMajor, versionFD.contents.lMinor,
    #                             versionFD.contents.lBuild))
    # print(c_char_p(versionFD.contents.Version).value.decode(u'utf-8'))
    # print(c_char_p(versionFD.contents.BuildDate).value.decode(u'utf-8'))
    # print(c_char_p(versionFD.contents.CopyRight).value.decode(u'utf-8'))

    hFREngine = c_void_p()
    ret = AFR_FSDK_InitialEngine(APPID, FR_SDKKEY, pFRWorkMem, c_int32(FR_WORKBUF_SIZE), byref(hFREngine))
    if ret != 0:
        AFD_FSDKLibrary.AFD_FSDK_UninitialFaceEngine(hFDEngine)
        CLibrary.free(pFDWorkMem)
        CLibrary.free(pFRWorkMem)
        print(u'AFR_FSDK_InitialEngine ret 0x{:x}'.format(ret))
        System.exit(0)

    # print FREngine version
    # versionFR = AFR_FSDK_GetVersion(hFREngine)
    # print(u'{} {} {} {}'.format(versionFR.contents.lCodebase, versionFR.contents.lMajor, versionFR.contents.lMinor,
    #                             versionFR.contents.lBuild))
    # print(c_char_p(versionFR.contents.Version).value.decode(u'utf-8'))
    # print(c_char_p(versionFR.contents.BuildDate).value.decode(u'utf-8'))
    # print(c_char_p(versionFR.contents.CopyRight).value.decode(u'utf-8'))

    dataset = 'facedata/faces/'
    face_in = 'face_detect/'
    # 加载人脸特征文件
    face = FaceBase()
    start = time.time()
    face.loadfacedata()
    start = time.time()
    # face.initFaceFromDir(hFDEngine, hFREngine, input_face)
    end = time.time()
    print('load faces feature use {0} s'.format(end - start))
    # face.savefacedata()

    list_face_base = os.listdir(dataset)
    list_face_detect = os.listdir(face_in)
    # 加载待识别的人脸照片
    for i in list_face_detect:
        filePathA = face_in + '/' + i
        inputImageA = loadImageData(filePathA)
        # 提取待检测的图片的人脸特征(最大人脸框的人脸)
        featureA = getFeatureFromImg(hFDEngine=hFDEngine, hFREngine=hFREngine, inputImg=inputImageA)
        if featureA == 0.0:
            print('extractFRFeature fail.')
            continue
        start = time.time()
        face_max_p = 0.0
        # p = c_float(0)
        face_max_name = 'Unknow'
        face_max_ID = 'Unknow'

        print('________________________________________________________________________')
        # print(face.getFaceData())

        # 人脸特征匹配
        # 从存放人脸特征的字典中获取所有图片的人脸信息(字典)
        for k, v in face.getFaceData():
            featureB = v['FaceFeature']
            if featureB == 0.0:
                print('extractFRFeature fail.You need to check the *.pkl file')
                continue

            # print(k)
            # print(featureB)
            # 逐个特征比较
            p = compareFeatureSimilarytey(hFREngine, featureA, featureB)
            print('{0}: {1}'.format(k,p.value))

            # 找到最大的人脸特征对应的Name
            pj = p.value
            # print(pj > face_max_p)
            if pj > face_max_p:
                face_max_p = p.value
                face_max_name = v['Name']

            # print('max_p {0}'.format(face_max_p))
        print('max_p {0}'.format(face_max_p))
        end = time.time()
        print(u'Compare Feature use time {0} s'.format(end - start))
        print(u'It is {0}'.format(face_max_name))
        print(u'Similarity score is:{0}'.format(face_max_p))
        featureA.freeUnmanaged()

    # release Engine
    AFD_FSDK_UninitialFaceEngine(hFDEngine)
    AFR_FSDK_UninitialEngine(hFREngine)

    CLibrary.free(pFDWorkMem)
    CLibrary.free(pFRWorkMem)

    print(u'#####################################################')
'''