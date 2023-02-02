import os

import video_utils
import ocr_utils
import yaml
import sys
from yaml.loader import SafeLoader


def vids_to_imgs(cfg):

    match = cfg['name']
    file_location = os.path.join('./videos', match+'.mp4')
    if os.path.exists(file_location):
        print('The match ', match, ' file exists!!')
    else:
        print('The match ', match, ' DOES NOT EXIST!!')

    time_of_ref = cfg['ref_frame']['time_of_ref']
    window_len = cfg['ref_frame']['window_len']
    ref_frame_loc = cfg['ref_frame']['ref_frame_loc']

    start_time = cfg['video']['start_time']
    end_time = cfg['video']['end_time']

    fps = cfg['fps']

    img_per_combine= cfg['overs_image']['img_per_combine']
    img_per_horizontal = cfg['overs_image']['img_per_horizontal']
    skip_frames = cfg['overs_image']['skip_frame']
    threshold = cfg['overs_image']['threshold']

    csv_loc = cfg['files']['csv_loc']
    image_loc = cfg['files']['image_loc']
    json_loc = cfg['files']['json_loc']
    metadata_loc = cfg['files']['metadata_loc']


    timestamp_info, list_framenum, H, W = video_utils.process_avi_pixels(file_location, time_of_ref = time_of_ref, 
            window_len=window_len, images_per_combine=img_per_combine, images_per_horizontal=img_per_horizontal,
            start_time=start_time, end_time =end_time, skip=skip_frames, threshold=threshold,
            fps= fps, name=match, out_folder=image_loc, ref_frame_loc = ref_frame_loc)

    video_utils.save_csv(timestamp_info, list_framenum, img_per_combine, csv_loc)

    timestamps_0, timestamps_1 = ocr_utils.ocr_to_json(image_loc, json_loc, metadata_loc, csv_loc, height=H, 
             width=W, is_highlight=True, img_per_row=img_per_horizontal, img_per_col = (img_per_combine // img_per_horizontal))



if __name__ == "__main__":
    # loc = './config/auckland_aces_v_central_stags.yaml'
    # with open(loc) as f:
    #     cfg = yaml.safe_load(f)
        # cfg = yaml.load(f, Loader = yaml.FullLoader)
    # print(cfg)
    # vids_to_imgs(cfg)
    pass
