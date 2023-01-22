import numpy as np
import cv2
import math
import os
import io
from google.cloud import vision
import sys

def get_ref_frame(vid_loc, time_sec, fps, window_sec, ref_frame_loc):
    client = vision.ImageAnnotatorClient()

    vc = cv2.VideoCapture(vid_loc)
    ret, frame = vc.read()

    name = vid_loc.split('/')
    name = name[-1][:-4]
    # print(loc)

    frame_shape = frame.shape
    h = 80
    w = 60
    Y1 = frame_shape[0] - h
    Y2 = frame_shape[0]
    X1 = frame_shape[1]//2 - w
    X2 = frame_shape[1]//2 + w

    vc.set(1, time_sec * fps - window_sec * fps)
    total_frame = 2*window_sec*fps

    framenum = 0
    while framenum < total_frame:
        if framenum % 5 == 0:
            ret, frame = vc.read()
            cropped_frame = frame[Y1:Y2, X1:X2].copy()
            new = cv2.imencode('.jpg', cropped_frame)[1].tostring()
            image = vision.Image(content=new)
            response = client.text_detection(image=image)
            texts = response.text_annotations

            vertices = []
            for text in texts[1:]:
                if text.description == 'OVERS':
                    for vertex in text.bounding_poly.vertices:
                        vertices.append([vertex.x, vertex.y])
                    break
            
            if len(vertices) > 0:
                y1 = vertices[0][1]
                y2 = vertices[2][1]
                x1 = vertices[0][0]
                x2 = vertices[2][0]
                new_crop = cropped_frame[y1:y2, x1:x2]
                bw_image = cv2.cvtColor(new_crop, cv2.COLOR_BGR2GRAY)
                number_of_black_pix = np.sum(bw_image < 100)
                if number_of_black_pix > 0.1*new_crop.shape[0]*new_crop.shape[1]:
                    if y2-y1<9:
                        y1 -= 1
                        y2 += 1
                    x1 = x1-10
                    x2 = x2+21

                    # x1 = x1-9
                    # x2 = x2+2

                    #### just get the over values, have the bounds chan
                    new_crop = cropped_frame[y1:y2, x1:x2]
                    coords = (X1 + x1, Y1 + y1, x2-x1, y2-y1)    #### (x, y, w, h)
                    print('Alright')
                    cv2.imwrite(ref_frame_loc + name + '_ref.jpg', new_crop)
                    # cv2.imwrite('test_ref.jpg', frame[coords[1]:coords[1]+coords[3], coords[0]:coords[0]+coords[2]])
                    return coords

        # print(framenum)
        framenum += 1

    print('!!!! Reference image not found')
    sys.exit()

if __name__ == '__main__':
    out = get_ref_frame('../ipl2017/IPL2017 M1.avi', 184, 25, 10, './')



