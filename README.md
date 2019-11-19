### ARC_Face
1. 该部分是门禁端的程序（原系统是包含门禁端、移动端、服务器端的，是一套连接手机应用app、服务器端管理和门禁端识别的整套系统）
2. 本程序包括：
#### 获取人脸的方式
- 从服务器端获得人脸到web_dataset目录
- 直接在本地添加人脸照片到face_base
#### 获取人脸特征文件
1. 在facedata/faces/目录下生成crop后的人脸
2. 提取crop后人脸的特征到facedata/faces/目录下的`.pkl`文件中
```
python crop_extract2pkl.py
```
#### 运行主程序
开启界面，检测人脸，与本地数据库人脸匹配，判断审核是否通过到界面上
```
python ui.py
```

### Requirement
1. Environment: ubuntu16.04 Python2.7
2. Package:
- imutils
- opencv-python
- dlib(pip install dlib -i https://pypi.douban.com/simple)
- PyQt4(sudo apt-get install python3-pyqt4)
- Pillow
- numpy
### Attention
SDK每年需要更新一次，到Arcsoft网上去重新申请SDK，并更新相应的2个so文件以及几个文件中的sdkkey的秘钥。(注意使用的是v1.1的版本，申请的时候会给
APPID，同时也会给出SDK KEY，里面包括FD/FT/FR/Age/Gender,复制FD和FR的KEY到程序中即可)
1. 下载SDK到本地，解压文件，在各自的目录下找到lib下的so文件
2. 将so文件放到readme.md同级目录下
    libarcsoft_fsdk_face_detection.so 
    libarcsoft_fsdk_face_recognition.so
3. 设置好APPID FD_SDKKEY
    ```
    APPID     = c_char_p(b'XXXXXXXXXX')
    FD_SDKKEY = c_char_p(b'YYYYYYYYYY')
    FR_SDKKEY = c_char_p(b'WWWWWWWWWW')
    ```
### Acknowledgement
整个系统是由5个小伙伴在2018年一起完成的，感谢大家为这个项目一起努力，最后还能获得比较好的成绩！
