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

# from deeptext_ocr import draw_utils
# file_name = os.path.abspath('IPL2017 M2_0.jpg')

# The name of the image file to annotate
# name = 'IPL2017 M2_0'
# file_name = name + '.jpg'
# input_folder = './images'
# output_folder = './images'

# image_cv2 = cv2.imread(os.path.join(input_folder, file_name))
# response = ocr_utils.extract_text(os.path.join(input_folder, file_name))
# texts = response.text_annotations

# print('Texts:')    
# for text in texts:        
#     print('\n"{}"'.format(text.description))        
#     vertices = (['({},{})'.format(vertex.x, vertex.y)                    
#                 for vertex in text.bounding_poly.vertices])        
#     # print('bounds: {}'.format(','.join(vertices)))
    
# debug_utils.draw_label_image(image_cv2, texts, output_folder, name)

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



    #### code snippet for saving some video clips
    # video_loc = '../ipl2017/' + cfg['name'] + '.mp4'
    # for i in range(len(start_secs)):
    #     loc = './snippets/' + cfg['name'] + '/' + str(i) + '/'
    #     if not os.path.exists(loc):
    #         os.makedirs(loc)
        
    #     target_vid_name = loc + 'snippet.mp4'
    #     extra = loc + 'extra.mp4'
    #     target_file_name = loc + 'annotation.txt'
    #     ffmpeg_extract_subclip(video_loc, start_secs[i], end_secs[i], targetname= target_vid_name)
    #     ffmpeg_extract_subclip(video_loc, rem_start[i], rem_end[i], targetname= extra)

    #     with open(target_file_name, 'w') as f:
    #         print("Over: %s\nRun: %s\nBowler: %s\nBatter: %s\n" % (
    #             overs[i], run[i], bowler[i], batter[i]), file=f)   ### comm[i]

    # with open(csv_loc + 'missing_balls.txt', 'w') as f:
    #     f.write(str(lost_balls))

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