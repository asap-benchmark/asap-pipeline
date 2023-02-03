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
from create_annotations import get_ann
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip



def main(cfg):
    ### Getting the timestamp for all overs present in our match
    vids_to_imgs(cfg)

    csv_loc = cfg['files']['csv_loc']

    with open(csv_loc + 'scraped_data_0.json') as f:
        scraped_0 = json.load(f)
    
    # with open(csv_loc + 'scraped_data_1.json') as f:
    #     scraped_1 = json.load(f)
    
    with open(csv_loc + 'match0.json') as f:
        match0 = json.load(f)
    
    with open(csv_loc + 'match1.json') as f:
        match1 = json.load(f)
    
    start = []
    start_secs = []
    end = []
    end_secs = []
    start_ms = []
    end_ms = []
    overs = []
    run = []
    bowler = []
    batter = []
    comm = []    ### CHANGE WHEN HAVE FULL COMMENTARY

    start_frame = []
    end_frame = []

    all_balls = np.arange(0.1, 50.1, 0.1)
    temp_overs = []
    rem_start = []
    rem_end = []
    lost_balls = []
    

    ### For first innings
    for i in match0.keys():
        print(i)
        if i in scraped_0.keys():
            start_sec = int(round(match0[i]['start'], 0))
            start_secs.append(start_sec)
            start.append(time.strftime("%H:%M:%S", time.gmtime(start_sec)))
            start_frame.append(match0[i]['start_frame'])
            end_sec = int(round(match0[i]['end'], 0))
            end_secs.append(end_sec)
            end.append(time.strftime("%H:%M:%S", time.gmtime(end_sec)))
            end_frame.append(match0[i]['end_frame'])

            rem_start.append(end_sec)
            rem_end.append(end_sec+1)

            start_ms.append('000')
            end_ms.append('000')

            temp_overs.append(i)
            overs.append(i)
            run.append(scraped_0[i]['run'])
            bowler.append(scraped_0[i]['bowler'])
            batter.append(scraped_0[i]['batter'])
            # comm.append(scraped_0[i]['comm'])   ### CHANGE WHEN FULL COMMENTARY
    
    temp_overs = []
    

    ### For second innings
    for i in match1.keys():
        print(i)
        if i in scraped_1.keys():
            start_sec = int(round(match1[i]['start'], 0))
            start_secs.append(start_sec)
            start.append(time.strftime("%H:%M:%S", time.gmtime(start_sec)))
            start_frame.append(match1[i]['start_frame'])
            end_sec = int(round(match1[i]['end'], 0))
            end_secs.append(end_sec)
            end.append(time.strftime("%H:%M:%S", time.gmtime(end_sec)))
            end_frame.append(match1[i]['end_frame'])

            rem_start.append(end_sec)
            rem_end.append(end_sec+1)

            start_ms.append('000')
            end_ms.append('000')
            
            temp_overs.append(i)
            overs.append(i)
            run.append(scraped_1[i]['run'])
            bowler.append(scraped_1[i]['bowler'])
            batter.append(scraped_1[i]['batter'])
            # comm.append(scraped_1[i]['comm'])     ### CHANGE WHEN FULL COMMENTARY



    # print(cfg['name'])
    annotations = get_ann(overs, run, start_frame, end_frame, bowler, batter, cfg)
    with open(csv_loc + cfg['name'] +'.json', 'w') as f:
        json.dump(annotations, f)
    
    df = pd.DataFrame(columns=['start', 'start_ms', 'end', 'end_ms', 'overs', 'run', 'bowler', 'batter'])  ##  'commentary'
    df.start = start
    df.start_ms = start_ms
    df.end = end
    df.end_ms = end_ms
    df.overs = overs
    df.run = run
    df.bowler = bowler
    df.batter = batter
    # df.commentary = comm   ### change this

    df.to_csv(csv_loc + 'overlay.csv', index=False)

    get_overlay(csv_loc, csv_loc + 'overlay.csv')




if __name__ == "__main__":
    loc = './config/auckland_aces_v_central_stags.yaml'
    with open(loc) as f:
        cfg = yaml.safe_load(f)
        # cfg = yaml.load(f, Loader = yaml.FullLoader)
    # print(cfg)
    main(cfg)