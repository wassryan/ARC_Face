import numpy as np
import cv2
import dlib
from scipy.spatial import distance
import os
# from imutils import face_utils

def eye_aspect_ratio(eye):
    # print(eye)
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

