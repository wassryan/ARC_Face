# -*- coding: UTF-8 -*-
from my_untils import *
from AFR_face import *
from my_untils.image_resize import *
from my_untils.FaceBase import *
import dlib

predictor_path = "./shape_predictor_68_face_landmarks.dat"
detect = dlib.get_frontal_face_detector()

predictor = dlib.shape_predictor(predictor_path)
rescale = [1.185974, 1.0, 1.135600, 1.17]

original_img='face_base/'
small_img='facedata/faces/'

if __name__==u'__main__':
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
		sys.exit(0)

	# print FREngine version
	versionFR = AFR_FSDK_GetVersion(hFREngine)
	print(u'{} {} {} {}'.format(versionFR.contents.lCodebase, versionFR.contents.lMajor, versionFR.contents.lMinor,
								versionFR.contents.lBuild))
	print(c_char_p(versionFR.contents.Version).value.decode(u'utf-8'))
	print(c_char_p(versionFR.contents.BuildDate).value.decode(u'utf-8'))
	print(c_char_p(versionFR.contents.CopyRight).value.decode(u'utf-8'))
	getSmallImg(original_img,small_img)
	face=FaceBase()
	# 加载 input_face 目录下的图片,批量提取特征
	face.initFaceFromDir(hFDEngine, hFREngine, small_img)
	# 将含有特征字典保存到文件
	face.savefacedata()
	face.freeAllFeature()
	print("----------------------------")
	print("人脸特征读取完成！")
	print("共获取人脸数：")
	print(face.size)
	# face.loadfacedata()

	# release Engine
	AFD_FSDK_UninitialFaceEngine(hFDEngine)
	AFR_FSDK_UninitialEngine(hFREngine)

	CLibrary.free(pFDWorkMem)
	CLibrary.free(pFRWorkMem)
