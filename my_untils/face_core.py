# -*- encoding=utf-8 -*-
from arcsoft import CLibrary, ASVL_COLOR_FORMAT, ASVLOFFSCREEN, c_ubyte_p, FaceInfo
from arcsoft.utils import BufferInfo, ImageLoader
from arcsoft.AFD_FSDKLibrary import *
from arcsoft.AFR_FSDKLibrary import *
from arcsoft import AFD_FSDKLibrary, AFR_FSDKLibrary
from ctypes import *
import traceback
from imutils import face_utils
from my_untils.eye_blink import *
from PyQt4.QtCore import *

APPID = c_char_p(b'FBmQrBiFKgDS4UenPAXXSmH4mWXSd6V5oq4yFc17YynT')
FD_SDKKEY = c_char_p(b'C4wd8EyQjD57EPbXuPmSBLjxwJpRMJPb66HjuwWitHE7')
FR_SDKKEY = c_char_p(b'C4wd8EyQjD57EPbXuPmSBLkTaus8JFvgpQRxuvRHQcC3')
FD_WORKBUF_SIZE = 20 * 1024 * 1024
FR_WORKBUF_SIZE = 40 * 1024 * 1024
MAX_FACE_NUM = 50
bUseYUVFile = False
bUseBGRToEngine = True

# 人脸检测算法
def doFaceDetection(hFDEngine, inputImg):
    faceInfo = []

    pFaceRes = POINTER(AFD_FSDK_FACERES)()

    # 初始化人脸检测引擎,具体执行代码在动态链接库中执行
    # 输入人脸检测图像,输出人脸检测信息
    ret = AFD_FSDK_StillImageFaceDetection(hFDEngine, byref(inputImg), byref(pFaceRes))
    if ret != 0:
        print(u'AFD_FSDK_StillImageFaceDetection 0x{0:x}'.format(ret))
        return faceInfo

    # 将检测到的人脸信息放在faceInfo中
    faceRes = pFaceRes.contents
    maxsize = 0.0  # 存放最大的矩形框大小
    maxi = 0  # 存放最大的矩形框编号
    if faceRes.nFace > 0:
        for i in range(0, faceRes.nFace):
            rect = faceRes.rcFace[i]
            orient = faceRes.lfaceOrient[i]
            faceInfo.append(FaceInfo(rect.left, rect.top, rect.right, rect.bottom, orient))
            size = (rect.right - rect.left) * (rect.bottom - rect.top)
            if maxsize < size:
                maxsize = size
                maxi = i

    return faceInfo, maxi

# 提取人脸特征
def extractFRFeature(hFREngine, inputImg, faceInfo):
    faceinput = AFR_FSDK_FACEINPUT()
    # 获取人脸检测框的位置
    faceinput.lOrient = faceInfo.orient
    faceinput.rcFace.left = faceInfo.left
    faceinput.rcFace.top = faceInfo.top
    faceinput.rcFace.right = faceInfo.right
    faceinput.rcFace.bottom = faceInfo.bottom

    faceFeature = AFR_FSDK_FACEMODEL()
    # 提取人脸特征
    ret = AFR_FSDK_ExtractFRFeature(hFREngine, inputImg, faceinput, faceFeature)
    if ret != 0:
        print(u'AFR_FSDK_ExtractFRFeature ret 0x{0:x}'.format(ret))
        return None

    try:
        return faceFeature.deepCopy()  # 返回深复制结果
    except Exception as e:
        traceback.print_exc()
        print(e.message)
        return None

def getFeatureFromImg(hFDEngine, hFREngine, inputImg):
    # Do Face Detect
    faceInfos, i = doFaceDetection(hFDEngine, inputImg)
    if len(faceInfos) < 1:
        print(u'no face in Image')
        return 0.0

    # Extract Face Feature 提取人脸特征
    faceFeature = extractFRFeature(hFREngine, inputImg, faceInfos[i])
    if faceFeature == None:
        print(u'extract face feature in Image faile')
        return 0.0

    return faceFeature  # 浅复制

def compareFeatureSimilarity(hFREngine, faceFeatureA, faceFeatureB):
    # calc similarity between faceA and faceB 计算两个人脸的相似度
    fSimilScore = c_float(0.0)
    ret = AFR_FSDK_FacePairMatching(hFREngine, faceFeatureA, faceFeatureB, byref(fSimilScore))

    # faceFeatureB.freeUnmanaged()
    if ret != 0:
        print(u'AFR_FSDK_FacePairMatching failed:ret 0x{0:x}'.format(ret))
        return c_float(0.0)
    return fSimilScore

def comparefaces(hFREngine, featureA, faceFeatureBase):
    face_max_p = 0.0
    face_max_name = 'Unknow'
    face_max_ID = 'Unknow'

    for k, v in faceFeatureBase:
        featureB = v['FaceFeature']
        if featureB == 0.0:
            print('extractFRFeature fail.')
            continue

        # 逐个特征比较
        p = compareFeatureSimilarity(hFREngine, featureA, featureB)

        # 找到最大的人脸特征对应的Name
        pj = p.value
        # print(pj > face_max_p)
        if pj > max(0.5, face_max_p):
            face_max_p = p.value
            face_max_name = v['Name']
            face_max_ID = k

    return face_max_p, face_max_name, face_max_ID

# 存放人脸识别结果 数据
class FRResult():
    def __init__(self, faceExist=False, faces=None, p=0.0, faceName='', faceID=''):
        self.faceExist = faceExist # 人脸是否存在
        self.faces = faces          # 检测到的人脸区域
        self.p = p                  # 置信度
        self.faceName = faceName    # 名字
        self.faceID = faceID        # ID

    # 返回数据
    def getData(self):
        return self.faceExist, self.faces, self.p, self.faceName, self.faceID

    # 修改数据
    def setData(self, faceExist, faces, p, faceName, faceID):
        self.faceExist = faceExist
        self.faces = faces
        self.p = p
        self.faceName = faceName
        self.faceID = faceID

class FRFace(QThread):

    def __init__(self, parent=None):
        super(FRFace, self).__init__(parent)
        self.updatefacebase = False  # 一个flag，是否需要更新本地数据库
        self.updatelists = []  # 从服务器获得的数据(ID\name\pic_path\option)
        from FaceBase import FaceBase
        self.facebase = FaceBase()  # 初始化人脸数据库
        self.facefrdata = FRResult()  # 人脸识别结果类：初始化存放人脸识别后返回的数据类:人脸是否存在、检测到的人脸区域、置信度、ID

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

    def setFrameSize(self, width, height):
        # 获取摄像头帧大小
        self.width = width
        self.height = height

    # 获取并转换帧数据
    def inputFrame(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # 格式转化
        self.image = GetVideoImage(frame, self.width, self.height)  # opencv 格式 -> SDK可以直接识别的格式

    def getUpdateData(self, updatelists):
        if len(updatelists) > 0:# 如果updatelists不为空，则确实需要更新数据库，令为True
            self.updatefacebase = True
            self.updatelists = updatelists

    # 执行人脸识别
    def run(self):
        image = self.image #opencv从摄像头中用读取到的帧并转化成sdk可识别的格式的image
        face_max_p = 0.0
        face_max_name = 'Unknow'
        face_max_ID = 'Unknow'

        try:
            faces, i = doFaceDetection(self.hFDEngine, image)# SDK人脸检测

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
    '''
    # 从服务器请求更新本地的图片
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

class FDFace():
    def __init__(self):

        shape_detector_path = './shape_predictor_68_face_landmarks.dat'
        self.detector = dlib.get_frontal_face_detector()  # 人脸检测器
        self.predictor = dlib.shape_predictor(shape_detector_path)  # 人脸特征点检测器

        # 定义一些参数
        self.EYE_AR_THRESH_HIGH = 0.3  # EAR阈值，大于0.3认为眼睛是睁开的
        self.EYE_AR_THRESH_LOW = 0.25  # EAR阈值，小于0.2认为眼睛是闭住的
        self.EYE_AR_CONSEC_FRAMES = 3  # 当EAR小于阈值时，接连多少帧才确保发生了发生眨眼动作
        # 对应特征点的序号
        self.RIGHT_EYE_START = 37 - 1
        self.RIGHT_EYE_END = 42 - 1
        self.LEFT_EYE_START = 43 - 1
        self.LEFT_EYE_END = 48 - 1

        self.blink_counter = 0  # 眨眼计数
        self.frame_counter = 0  # 连续帧计数

        self.Trueface = False
        self.faceDetected = False
    # 只检测该帧是否有人脸，不识别
    def detectFace(self, frame):
        frame_output = frame
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = self.detector(frame_gray, 0)  # 调用dlib人脸检测

        # frame_counter = 0  # 连续帧计数
        # blink_counter = 0  # 眨眼计数
        count = 0
        name = 'Unknown'
        confidence = 0

        if len(rects) < 1:
            self.blink_counter = 0  # 眨眼计数清零
            self.frame_counter = 0  # 连续帧计数清零
            self.Trueface = False
            self.faceDetected = False

        for rect in rects:
            self.faceDetected = True
            left, right, top, bottom = rect.left(), rect.right(), rect.top(), rect.bottom()
            shape = self.predictor(frame_gray, rect)  # 检测特征点

            points = face_utils.shape_to_np(shape)  # convert the facial landmark (x, y)-coordinates to a NumPy array
            leftEye = points[self.LEFT_EYE_START:self.LEFT_EYE_END + 1]  # 取出左眼对应的特征点
            rightEye = points[self.RIGHT_EYE_START:self.RIGHT_EYE_END + 1]  # 取出右眼对应的特征点
            leftEAR = eye_aspect_ratio(leftEye)  # 计算左眼EAR
            rightEAR = eye_aspect_ratio(rightEye)  # 计算右眼EAR
            # print('leftEAR = {0}'.format(leftEAR))
            # print('rightEAR = {0}'.format(rightEAR))
            ear = (leftEAR + rightEAR) / 2.0  # 求左右眼EAR的均值
            frame_output = cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

            # 如果EAR小于阈值，开始计算连续帧，只有连续帧计数超过EYE_AR_CONSEC_FRAMES时，才会计做一次眨眼
            if ear < self.EYE_AR_THRESH_LOW:
                self.frame_counter += 1
            else:# 只有闭眼到一定帧数，再睁开眼，才会检测到人脸
                if self.frame_counter >= self.EYE_AR_CONSEC_FRAMES:
                    self.blink_counter += 1
                    count += 1
                    self.Trueface = True
                self.frame_counter = 0
            continue
        return frame_output, self.faceDetected, self.Trueface

# 加载YUV图像
def loadYUVImage(yuv_filePath, yuv_width, yuv_height, yuv_format):
    yuv_rawdata_size = 0

    inputImg = ASVLOFFSCREEN()
    inputImg.u32PixelArrayFormat = yuv_format
    inputImg.i32Width = yuv_width
    inputImg.i32Height = yuv_height
    if ASVL_COLOR_FORMAT.ASVL_PAF_I420 == inputImg.u32PixelArrayFormat:
        inputImg.pi32Pitch[0] = inputImg.i32Width
        inputImg.pi32Pitch[1] = inputImg.i32Width // 2
        inputImg.pi32Pitch[2] = inputImg.i32Width // 2
        yuv_rawdata_size = inputImg.i32Width * inputImg.i32Height * 3 // 2
    elif ASVL_COLOR_FORMAT.ASVL_PAF_NV12 == inputImg.u32PixelArrayFormat:
        inputImg.pi32Pitch[0] = inputImg.i32Width
        inputImg.pi32Pitch[1] = inputImg.i32Width
        yuv_rawdata_size = inputImg.i32Width * inputImg.i32Height * 3 // 2
    elif ASVL_COLOR_FORMAT.ASVL_PAF_NV21 == inputImg.u32PixelArrayFormat:
        inputImg.pi32Pitch[0] = inputImg.i32Width
        inputImg.pi32Pitch[1] = inputImg.i32Width
        yuv_rawdata_size = inputImg.i32Width * inputImg.i32Height * 3 // 2
    elif ASVL_COLOR_FORMAT.ASVL_PAF_YUYV == inputImg.u32PixelArrayFormat:
        inputImg.pi32Pitch[0] = inputImg.i32Width * 2
        yuv_rawdata_size = inputImg.i32Width * inputImg.i32Height * 2
    elif ASVL_COLOR_FORMAT.ASVL_PAF_RGB24_B8G8R8 == inputImg.u32PixelArrayFormat:
        inputImg.pi32Pitch[0] = inputImg.i32Width * 3
        yuv_rawdata_size = inputImg.i32Width * inputImg.i32Height * 3
    else:
        print(u'unsupported  yuv format')
        exit(0)

    # load YUV Image Data from File
    f = None
    try:
        f = open(yuv_filePath, u'rb')
        imagedata = f.read(yuv_rawdata_size)
    except Exception as e:
        traceback.print_exc()
        print(e.message)
        exit(0)
    finally:
        if f is not None:
            f.close()

    if ASVL_COLOR_FORMAT.ASVL_PAF_I420 == inputImg.u32PixelArrayFormat:
        inputImg.ppu8Plane[0] = cast(imagedata, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(
            addressof(inputImg.ppu8Plane[0].contents) + (inputImg.pi32Pitch[0] * inputImg.i32Height), c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(
            addressof(inputImg.ppu8Plane[1].contents) + (inputImg.pi32Pitch[1] * inputImg.i32Height // 2), c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    elif ASVL_COLOR_FORMAT.ASVL_PAF_NV12 == inputImg.u32PixelArrayFormat:
        inputImg.ppu8Plane[0] = cast(imagedata, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(
            addressof(inputImg.ppu8Plane[0].contents) + (inputImg.pi32Pitch[0] * inputImg.i32Height), c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    elif ASVL_COLOR_FORMAT.ASVL_PAF_NV21 == inputImg.u32PixelArrayFormat:
        inputImg.ppu8Plane[0] = cast(imagedata, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(
            addressof(inputImg.ppu8Plane[0].contents) + (inputImg.pi32Pitch[0] * inputImg.i32Height), c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    elif ASVL_COLOR_FORMAT.ASVL_PAF_YUYV == inputImg.u32PixelArrayFormat:
        inputImg.ppu8Plane[0] = cast(imagedata, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    elif ASVL_COLOR_FORMAT.ASVL_PAF_RGB24_B8G8R8 == inputImg.u32PixelArrayFormat:
        inputImg.ppu8Plane[0] = cast(imagedata, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    else:
        print(u'unsupported yuv format')
        exit(0)

    inputImg.gc_ppu8Plane0 = imagedata
    return inputImg

# 加载图片文件
def loadImage(filePath):
    inputImg = ASVLOFFSCREEN()
    if bUseBGRToEngine:
        bufferInfo = ImageLoader.getBGRFromFile(filePath)
        inputImg.u32PixelArrayFormat = ASVL_COLOR_FORMAT.ASVL_PAF_RGB24_B8G8R8
        inputImg.i32Width = bufferInfo.width
        inputImg.i32Height = bufferInfo.height
        inputImg.pi32Pitch[0] = bufferInfo.width * 3
        inputImg.ppu8Plane[0] = cast(bufferInfo.buffer, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    else:
        bufferInfo = ImageLoader.getI420FromFile(filePath)
        inputImg.u32PixelArrayFormat = ASVL_COLOR_FORMAT.ASVL_PAF_I420
        inputImg.i32Width = bufferInfo.width
        inputImg.i32Height = bufferInfo.height
        inputImg.pi32Pitch[0] = inputImg.i32Width
        inputImg.pi32Pitch[1] = inputImg.i32Width // 2
        inputImg.pi32Pitch[2] = inputImg.i32Width // 2
        inputImg.ppu8Plane[0] = cast(bufferInfo.buffer, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(
            addressof(inputImg.ppu8Plane[0].contents) + (inputImg.pi32Pitch[0] * inputImg.i32Height), c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(
            addressof(inputImg.ppu8Plane[1].contents) + (inputImg.pi32Pitch[1] * inputImg.i32Height // 2), c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    inputImg.gc_ppu8Plane0 = bufferInfo.buffer

    return inputImg

def loadImageData(path):
    # load Image Data
    if bUseYUVFile:
        filePathA = path
        yuv_widthA = 640
        yuv_heightA = 480
        yuv_formatA = ASVL_COLOR_FORMAT.ASVL_PAF_I420

        return loadYUVImage(filePathA, yuv_widthA, yuv_heightA, yuv_formatA)

    else:
        filePath = path
        return loadImage(filePath)

def GetVideoImage(frame, width, height):
# 格式转化已解决
    inputImg = ASVLOFFSCREEN()
    if bUseBGRToEngine:
        bufferInfo = ImageLoader.getBGRFromFrame(frame, width, height)
        inputImg.u32PixelArrayFormat = ASVL_COLOR_FORMAT.ASVL_PAF_RGB24_B8G8R8
        inputImg.i32Width = width
        inputImg.i32Height = height
        inputImg.pi32Pitch[0] = width*3
        inputImg.ppu8Plane[0] = cast(bufferInfo.buffer, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    else:
        bufferInfo = ImageLoader.getI420FromFrame(frame, width, height)
        inputImg.u32PixelArrayFormat = ASVL_COLOR_FORMAT.ASVL_PAF_I420
        inputImg.i32Width = bufferInfo.width
        inputImg.i32Height = bufferInfo.height
        inputImg.pi32Pitch[0] = inputImg.i32Width
        inputImg.pi32Pitch[1] = inputImg.i32Width // 2
        inputImg.pi32Pitch[2] = inputImg.i32Width // 2
        inputImg.ppu8Plane[0] = cast(bufferInfo.buffer, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(addressof(inputImg.ppu8Plane[0].contents) + (inputImg.pi32Pitch[0] * inputImg.i32Height), c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(addressof(inputImg.ppu8Plane[1].contents) + (inputImg.pi32Pitch[1] * inputImg.i32Height // 2), c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    inputImg.gc_ppu8Plane0 = bufferInfo.buffer

    return inputImg