import cv2
import numpy as np
import math
from get_reference_frame import get_ref_frame
import os
import csv

def pixel_distance(img1, img2):
    '''
    Get the histogram of an image. For an 8-bit, grayscale image, the
    histogram will be a 256 unit vector in which the nth value indicates
    the percent of the pixels in the image with the given darkness level.
    The histogram's values sum to 1.
    '''
    img1 = img1.astype(np.int16)
    img2 = img2.astype(np.int16)

    return np.sum(np.absolute(np.subtract(img1.flatten(), 
        img2.flatten())))

# def pixel_distance(img1, img2):
#     '''
#     Get the histogram of an image. For an 8-bit, grayscale image, the
#     histogram will be a 256 unit vector in which the nth value indicates
#     the percent of the pixels in the image with the given darkness level.
#     The histogram's values sum to 1.
#     '''
#     # img1 = img1.astype(np.int16)
#     # img2 = img2.astype(np.int16)

#     bw_image_1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
#     bw_image_2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

#     return np.absolute(np.sum(bw_image_1) - np.sum(bw_image_2))

# def pixel_distance(img1, img2):
#     '''
#     Get the histogram of an image. For an 8-bit, grayscale image, the
#     histogram will be a 256 unit vector in which the nth value indicates
#     the percent of the pixels in the image with the given darkness level.
#     The histogram's values sum to 1.
#     '''
#     # img1 = img1.astype(np.int16)
#     # img2 = img2.astype(np.int16)

#     bw_image_1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
#     bw_image_2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

#     black_pix_1 = np.sum(bw_image_1 < 75)
#     black_pix_2 = np.sum(bw_image_2 < 75)
#     return np.absolute(black_pix_1 - black_pix_2)


# function for taking frames from video and combining into video to save # images sent to OCR
def combine_images(images, num_images: int, num_horizontal: int):
    '''
    Return a new image with the images glued together
    Arguments:
        images: N x H x W ndarray of images
        num_horizontal: determines the number of images to put next to each other
        on the same row
    '''
    combined_image = None
    for i in range (math.ceil(num_images / num_horizontal)):
        row_image = None
        for j in range (num_horizontal):
            if row_image is None:
                row_image = images[i*num_horizontal + j]
            elif (i*num_horizontal + j >= num_images):
                row_image = cv2.hconcat([row_image, np.zeros((images.shape[1],images.shape[2],3), np.uint8)])
            else:
                row_image = cv2.hconcat([row_image, images[i*num_horizontal + j]])

        if combined_image is None:
            combined_image = row_image
        else:
            combined_image = cv2.vconcat([combined_image, row_image])

    return combined_image
    


def process_avi_pixels(file_location, time_of_ref=200, window_len=10,
    images_per_combine:int=240, images_per_horizontal:int=12, start_time=None, end_time=None,
    skip=20, threshold=60, fps=25, name=None, out_folder=None, ref_frame_loc=None):
    ''' 
    Function for taking avi and grabbing cropped frames (fixed) from them
    '''
    ## Getting the reference frame to compare with
    #### !!! This was required for automatically getting ref frame !!!
    # x, y, w, h = get_ref_frame(file_location, time_of_ref, fps, window_len, ref_frame_loc)
    vc = cv2.VideoCapture(file_location)
    ret, frame = vc.read()
    print(frame.shape)
    vc.set(1, 63900)
    x = 69
    y = 321
    w = 87
    h = 21
    ret, frame = vc.read()
    # print(frame.shape)
    cv2.imwrite(ref_frame_loc + name + '_ref.jpg', frame[y:y+h, x:x+w])


    vc = cv2.VideoCapture(file_location)
    compare_frame = None # this frame is what we compare for skipping
    if vc.isOpened():
        rval, frame = vc.read()
    else:
        rval = False

    timestamps = [] # dictionary mapping from crop to frame
    list_timestamps = [] # list of composite dictionary mappings
    framenum_li = []
    all_framenum_li = []
    frames = None
    time_window = None
    curr_time_window_cnt = 0

    if start_time is not None:
        start = start_time * fps
    else:
        start = 0
    
    end = end_time * fps

    # frame num, num frames processed, num images generated
    framenum, cnt, cnt_composite = 0, 0, 0 

    # loop to start of time window of interest
    while (framenum < start):
        rval, frame = vc.read()
        framenum += 1
    # compare_frame = frame[y:y+h, x:x+w].copy()
    compare_frame = cv2.imread(ref_frame_loc + name + '_ref.jpg')

    while framenum < end:
        # process every 'skip'th frame
        for i in range (skip):
            rval, frame = vc.read()
            framenum += 1
        
        if frame is None:
            return list_timestamps

        # skip frames disimilar to what we want
        # calibrate treshold for pixel similarity
        while ((pixel_distance(compare_frame, frame[y:y+h, x:x+w]) / (w*h*3)) > threshold):
            rval, frame = vc.read()
            framenum += 1
            if frame is None:
                return list_timestamps

        if frame is None:
            return list_timestamps
        # while (pixel_distance(compare_frame, frame[y:y+h, x:x+w]) > 10):
        #     rval, frame = vc.read()
        #     framenum += 1
        
        # cv2.imwrite('test.jpg', frame)
        # print(frame.shape)
        # if cnt==21:
        #     cv2.imwrite('test1.jpg', frame[y:y+h, x:x+w])
        #     print(framenum)
        # if cnt==22:
        #     cv2.imwrite('test2.jpg', frame[y:y+h, x:x+w])
        #     print(framenum)
        cropped_frame = frame[y:y+h, x:x+w].copy()
        bordersize = 8
        padded_frame = cv2.copyMakeBorder(
            cropped_frame,
            top=bordersize,
            bottom=bordersize,
            left=bordersize,
            right=bordersize,
            borderType=cv2.BORDER_CONSTANT,
            value=[255, 255, 255]
        )

        cropped_frame = np.expand_dims(padded_frame, axis=0)
        cnt += 1
        timestamps.append(framenum / fps)
        framenum_li.append(framenum)
        # timestamps[cnt % images_per_combine] = framenum # map index to current timestamp

        if frames is None:
            frames = cropped_frame.copy()
        else:
            frames = np.concatenate((frames, cropped_frame), axis=0)

        if (cnt % images_per_combine == 0):
            new_image = combine_images(frames, images_per_combine, images_per_horizontal)
            list_timestamps.append(timestamps)
            all_framenum_li.append(framenum_li)
            timestamps = []
            framenum_li = []

            # send to ocr here
            if not os.path.exists(out_folder):
                os.makedirs(out_folder)

            path = os.path.join(out_folder, name + "_" + str(cnt_composite) + ".jpg")
            cv2.imwrite(path, new_image)
            cnt_composite += 1

            print('Image: ', path, ' SAVED')

            frames = None # reset frames

        # for debugging purposes
        # if (cnt > images_per_combine):
        #     return list_timestamps

    remaining_frames = images_per_combine - frames.shape[0]
    white_frames = np.full((remaining_frames, frames.shape[1], frames.shape[2], frames.shape[3]), 255)

    frames = np.concatenate((frames, white_frames), axis=0)
    new_image = combine_images(frames, images_per_combine, images_per_horizontal)
    list_timestamps.append(timestamps)
    all_framenum_li.append(framenum_li)
    # print(image.shape[0])
    # print(image.shape[1])
    timestamps = {}

    # send to ocr here

    path = os.path.join(out_folder, name + "_" + str(cnt_composite) + ".jpg")
    cv2.imwrite(path, new_image)
    cnt_composite += 1

    frames = None # reset frames
    vc.release()
    return list_timestamps, all_framenum_li, new_image.shape[0], new_image.shape[1]


# function for converting video into frames of images using pixel coordinates for crop
# input is based on ratios instead of raw pixel coords
# def process_avi_pixels_ratios(file_location, img_width, img_height, x, y, w, h, images_per_combine:int=64, 
#     images_per_horizontal:int=8, seconds_of_interest=None, skip=120,
#     fps=25, save_images=False, name='ipl'):

#     assert x <= 1 and x >= 0 and y <= 1 and y >= 0 and w <= 1 and w >= 0 and h <= 1 and h >= 0
#     assert x+w <= 1 and x+w >= 0 and y+h <= 1 and y+h >= 0

#     a_x = math.ceil(img_width * x)
#     a_y = math.ceil(img_height * y)
#     a_w = math.ceil(img_width * w)
#     a_h = math.ceil(img_height * h)

#     process_avi_pixels(file_location, a_x, a_y, a_w, a_h, images_per_combine, images_per_horizontal,
#     seconds_of_interest, skip, fps, save_images, name)

def save_csv(list_of_timestamps, list_framenum, img_per_comp, name):
    '''
    Save a csv
    Arguments:
        list_of_timestamps: list of dictionaries, with each dictionary mapping
        an image in the crop (row-major order) to a timestamp
        img_per_crop: number of images in each crop
        name: path/name to save the csv to/as
    '''
    if not os.path.exists(name):
        os.makedirs(name)
    num_comps = len(list_of_timestamps)
    with open(name + 'run1.csv', mode='w') as csv_file:
        fieldnames = ['cmpid', 'imgid', 'time', 'frame']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for i in range (num_comps):
            num_imgs = len(list_of_timestamps[i])
            for j in range(num_imgs):
                # print(str(i) + ' , ' + str(j))
                writer.writerow({'cmpid': i, 'imgid': j, 'time': list_of_timestamps[i][j], 'frame': list_framenum[i][j]})


# save timestamp information as JSON
def save_json (list_of_timestamps):
    pass