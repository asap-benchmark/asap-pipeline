import io
import os
import cv2
import csv
import json
import re
import glob
import numpy as np
import pandas as pd

# Imports the Google Cloud client library
from google.cloud import vision

# vision-api client
client = vision.ImageAnnotatorClient()

def extract_text(path):
    """Detects English text in an image."""

    # Loads the image into memory
    with io.open(path, 'rb') as image_file:
        content = image_file.read()
        
    image = vision.Image(content=content)
    image_context = vision.ImageContext(language_hints=['en'])

    # Performs label detection on the image file
    response = client.text_detection(image=image, image_context=image_context)

    return response


def get_overs_position (texts):
    """ Get position of overs from OCR call. Input is OCR text_detection.
    Output is a list of (x,y,text) tuples where text strips all non-decimal characters """
    # texts = response.text_annotations
    positions = []
    # re_decimal = re.compile(r'[^\d.]+')
    max_len = len(texts)
    i = 0
    while i < max_len:
        text = texts[i]
        x, y, sz = 0, 0, 0
        if text.description == 'OVERS':
            new_text = texts[i+1]
            for vertex in new_text.bounding_poly.vertices:
                x += vertex.x
                y += vertex.y
                sz += 1
            x /= sz
            y /= sz
            try:
                if new_text.description == 'O':
                    over_num = 0.0
                else:
                    over_num = float(new_text.description)
                positions.append((x, y , over_num))
                i+=2
            except:
                i+=2
        else:
            i+=1

    # for text in texts:
    #     x, y, sz = 0,0,0
    #     for vertex in text.bounding_poly.vertices:
    #         x += vertex.x
    #         y += vertex.y
    #         sz += 1
    #     x /= sz
    #     y /= sz
    #     desc = re_decimal.sub('', text.description)
    #     if (desc != ''):
    #         positions.append((x,y,desc))
    # print(positions)
    return positions

def get_new_overs_position(texts):
    """ Get position of overs from OCR call. Input is OCR text_detection.
    Output is a list of (x,y,text) tuples where text strips all non-decimal characters """
    # texts = response.text_annotations
    positions = []
    re_decimal = re.compile(r'[^\d.]+')
    max_len = len(texts)
    i = 0

    while i < max_len:
        text = texts[i]
        # if '/37' in texts[i]:
        x, y, sz = 0, 0, 0
        if '/' in text.description:
            try:
                new_text = texts[i+1]
            except:
                i+=1
                pass
            for vertex in new_text.bounding_poly.vertices:
                x += vertex.x
                y += vertex.y
                sz += 1
            x /= sz
            y /= sz
            try:
                if new_text.description == 'O':
                    over_num = 0.0
                else:
                    over_num = float(new_text.description)
                positions.append((x, y , over_num))
                i+=2
            except:
                i+=2
        else:
            i+=1
    # for text in texts:
    #     x, y, sz = 0,0,0
    #     for vertex in text.bounding_poly.vertices:
    #         x += vertex.x
    #         y += vertex.y
    #         sz += 1
    #     x /= sz
    #     y /= sz
    #     desc = re_decimal.sub('', text.description)
    #     if (desc != ''):
    #         positions.append((x,y,desc))
    # # print(positions)
    return positions
        

# def position_to_index (bounding_boxes, width, height, img_per_row, img_per_col, cmpid):
#     """ Return index in image corresponding to bounding boxes """
#     indices = []
#     for box in bounding_boxes:
#         x,y,text = box
#         i = np.floor (x / (width / img_per_row)).astype(int)
#         j = np.floor (y / (height / img_per_col)).astype(int)
#         indices.append((cmpid, j, i, text))
#     # sort indices by row index
#     indices = sorted(indices, key=lambda tup: (tup[0],tup[1],tup[2]))
#     print(indices)
#     return indices

def position_to_index (bounding_boxes, width, height, img_per_row, img_per_col, cmpid):
    """ Return index in image corresponding to bounding boxes """
    indices = []
    for box in bounding_boxes:
        x,y,text = box
        i = np.floor (x / (width / img_per_row)).astype(int)
        j = np.floor( y / (height / img_per_col)).astype(int)
        indices.append((cmpid, j, i, text))
    # sort indices by row index
    indices = sorted(indices, key=lambda tup: (tup[0],tup[1],tup[2]))
    # print(indices)
    return indices


def indices_to_start_end (list_of_indices, is_highlight):
    """  Return start and end timestamps for each over """
    if len(list_of_indices) == 0:
        return []
    if len(list_of_indices[0]) == 0:
        return []

    start_end_timestamps = []
    first_cmp_idx, first_row_idx, first_col_idx, curr_overs  = list_of_indices[0][0]
    start_index = curr_index = (first_cmp_idx, (first_row_idx, first_col_idx))
    needs_correction = False
    corrected_over = 0.0

    # overs should be a float, starts as a string
    curr_overs = float(curr_overs)
    # if the decimal point is missed
    if curr_overs > 150:
        curr_overs /= 10

    # loop over all indices
    for indices in list_of_indices:
        # (cmpid, index_in_image, overs)
        for index in indices:
            cmpid, idx_row, idx_col, overs = index

            # very specific case where overs isn't a number
            if overs == "":
                if needs_correction:
                    needs_correction = False
                    curr_overs = corrected_over          
                start_end_timestamps.append((start_index, curr_index, "{:.1f}".format(curr_overs)))
                curr_overs = overs
                start_index = curr_index = (cmpid,(idx_row, idx_col))
            
            # try:
            overs = float(overs)
            # except:
            #     continue
            if overs > 150:
                overs /= 10
            
            # check if retrieved over is same as current
            if curr_overs == overs:
                curr_index = (cmpid, (idx_row, idx_col))
            else:
                # if an new over number appears for more than 1 frame, consider it
                if (start_index != curr_index):
                    # if not continuous (e.g. not +.1, or higher integer)
                    if not is_highlight:
                        # if the previous overs were corrected, now consider updating the rest
                        if needs_correction:
                            # don't correct yet in case errors pop up again for same over
                            if (corrected_over == overs):
                                continue
                            needs_correction = False
                            curr_overs = corrected_over          
                        
                        if not ((overs - curr_overs == 0.1) or (overs == 0.0) \
                        or (int(overs) - int(curr_overs) == 1 and overs.is_integer())):
                            # TODO: refine this logic later, esp since it's not always + 0.1
                            needs_correction = True
                            if int(overs) == int(curr_overs) or int(overs)//10 == int(curr_overs):
                                corrected_over = curr_overs + 0.1
                            else:
                                corrected_over = float(int(curr_overs))

                    start_end_timestamps.append((start_index, curr_index, "{:.1f}".format(curr_overs)))
                curr_overs = overs
                start_index = curr_index = (cmpid,(idx_row, idx_col))

    return start_end_timestamps


        

def ocr_to_json (image_folder, json_file, metadata_file, output_csv_file, height, width, is_highlight, img_per_row=12, img_per_col=20):
    """Convert OCR to JSON file"""
    indices = []
    cmp_id = 0
    for image_path in sorted(glob.glob(image_folder + '*.jpg'), key=os.path.getmtime):
        print(image_path)
        ocr_response = extract_text(image_path)
        # print(ocr_response)
        text = ocr_response.text_annotations
        bboxes = get_new_overs_position(text[1:]) # first index is dummy
        indices.append(position_to_index(bboxes, width, height, img_per_row, img_per_col, cmp_id))
        cmp_id += 1
    
    # write to csv file
    num_comps = len(indices)
    with open(output_csv_file + 'run1o.csv', mode='w') as csv_file:
        fieldnames = ['cmpid', 'row', 'col', 'overs']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for i in range (num_comps): 
            # print(i)
            # print(indices[i])
            for (j,ind) in enumerate(indices[i]):
                writer.writerow({'cmpid': ind[0], 'row': ind[1], 'col': ind[2], 'overs': ind[3]})

    # gather bbox to timestamp mappings
    start_end_timestamps = indices_to_start_end(indices, is_highlight)
    print(start_end_timestamps)
    timestamps_0 = {}
    timestamps_1 = {}

    # write to timestamp json
    df = pd.read_csv(metadata_file + 'run1.csv')
    # with open(output_csv_file + 'run_timestamps.csv', mode='w') as csv_file:
    #     fieldnames = ['over', 'start', 'end']
    #     writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    #     writer.writeheader()
    prev_overs = None
    idx = 0
    for start, end, overs in start_end_timestamps:
        (start_cmpid, start_id) = start
        (end_cmpid, end_id) = end
        start_row, start_col = start_id
        end_row, end_col = end_id

        # print("Found new print")
        # print(start_id)
        # print(end_id)

        start_time = df['time'][start_cmpid * (img_per_row * img_per_col) + start_row * img_per_row + start_col]
        end_time = df['time'][end_cmpid * (img_per_row * img_per_col) + end_row * img_per_row + end_col]
        # print(end_cmpid * (img_per_row * img_per_col) + end_row * img_per_row + end_col)

        start_frame = int(df['frame'][start_cmpid * (img_per_row * img_per_col) + start_row * img_per_row + start_col])
        end_frame = int(df['frame'][end_cmpid * (img_per_row * img_per_col) + end_row * img_per_row + end_col])
        overs = float(overs)

        if prev_overs == None and idx == 0:
            prev_overs = overs
            if overs not in timestamps_0:
                timestamps_0[overs] = {"start": start_time, "end": end_time, 'start_frame': start_frame, 'end_frame': end_frame}
            continue
        if prev_overs == 80.4:
            idx = 1
            if overs not in timestamps_1:
                timestamps_1[overs] = {"start": start_time, "end": end_time, 'start_frame': start_frame, 'end_frame': end_frame}
            prev_overs = overs
            continue
        if idx == 0:
            if overs not in timestamps_0:
                timestamps_0[overs] = {"start": start_time, "end": end_time, 'start_frame': start_frame, 'end_frame': end_frame}
        if idx == 1:
            if overs not in timestamps_1:
                timestamps_1[overs] = {"start": start_time, "end": end_time, 'start_frame': start_frame, 'end_frame': end_frame}
        prev_overs = overs
            
        
        # if overs not in timestamps:
        #     timestamps[overs] = {"start": start_time, "end": end_time}
        # writer.writerow({'over': overs, 'start': start_time, 'end': end_time})

    with open(json_file+'match0.json', 'w') as f:
        json.dump(timestamps_0,f)
    
    with open(json_file+'match1.json', 'w') as f:
        json.dump(timestamps_1,f)

    return timestamps_0, timestamps_1