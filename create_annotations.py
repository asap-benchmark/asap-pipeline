import io
import os
import cv2
import debug_utils
import ocr_utils
import yaml
import json
import numpy as np
from convert_vid_to_imgs import vids_to_imgs
from convert_to_srt import get_overlay
import datetime
import pandas as pd
import time
import re


# def get_num_run(run):
#     runs = run.split()
#     if len(runs)>1:
#         num = 0
#         for i in range(len(runs)):
#             if runs[i] == '•':
#                 num += 0
#                 continue

#             if 'w' in runs[i]:
#                 wide = 1
#             elif 'W' in runs[i]:
#                 bowled = 1
            
#             temp = re.sub('\D', '', runs[i])
#             num += int(temp)


def get_ann(overs, run, start_frame, end_frame, bowler, batter, cfg, num_balls = 1):
    annotations = []
    i = 0
    unique_run = []
    for i in range(len(overs)):
        ann = []
        bowled = 0
        wide = 0
        # print(cfg['name'])
        ann.append(cfg['name'])
        ann.append(float(overs[i]))
        ann.append(int(start_frame[i]))
        ann.append(int(end_frame[i]))
        ann.append(batter[i])
        ann.append(bowler[i])
        # run = 0
        # run = get_num_run(run[i])

        runs = run[i].split()
        num = 0
        for i in range(len(runs)):
            if runs[i] == '•':
                num += 0
                continue

            if 'w' in runs[i]:
                wide = 1
            elif 'W' in runs[i]:
                bowled = 1
            
            temp = re.sub('\D', '', runs[i])
            if temp == '':
                num += 0
                continue
            num += int(temp)
        
        ann.append(num)           ### the runs scored
        # if num not in unique_run.keys():
        #     unique_run[num] = 0
        # else:
        #     unique_run[num] += 1

        ques = []
        scored_any = 0
        if num>0:
            scored_any = 1
        
        if scored_any:
            ques.append('SCORED')
        else:
            ques.append('NOT-SCORED')
        
        if bowled:
            ques.append('OUT')
        else:
            ques.append('NOT-OUT')
        
        if wide:
            ques.append('WIDE')
        else:
            ques.append('NOT-WIDE')
        # ques.append(scored_any)
        # ques.append(bowled)
        # ques.append(wide)
        ques.append(num)
        # ques.append(num_balls)

        if ques not in unique_run:
            unique_run.append(ques)

        ann.append(ques)

        annotations.append(ann)
    
    print(unique_run)
    print(len(unique_run))
    return annotations
