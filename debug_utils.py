import os
import cv2

# TODO: Somehow attach timestamp to each relevant frame
# function for converting video into frames of images using pixel coordinates for crop
def draw_label_image (image, annotations, output_folder, image_name):
    for text in annotations:
        bounds = text.bounding_poly.vertices
        top_left = (bounds[0].x, bounds[0].y)
        bot_right = (bounds[2].x, bounds[2].y)
        cv2.rectangle(image, top_left, bot_right, (0, 255, 0), 2)  # green box (BGR)
        cv2.putText(image, text.description, top_left, cv2.FONT_HERSHEY_PLAIN, 0.6, (255, 0, 0), 1, cv2.LINE_AA)

    out_path = os.path.join(output_folder, image_name + ".png")
    ret = cv2.imwrite(image_name + ".png", image)

    if not ret:
        print(f"Couldn't Write: {out_path}")