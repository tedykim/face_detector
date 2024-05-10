import cv2
import dlib
import sys
import numpy as np
######################### 전체적으로 2.1보다 느리게 수행되고, ryan이 마지막에 위치못찾음 
######################### Dad_daughter 수행은되나 ryan_tran..이 안 나옴
scaler = 0.3

# initialize face detector and shape predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('models/shape_predictor_68_face_landmarks.dat')

# load video
cap = cv2.VideoCapture('samples/daughter.mp4')
# load overlay image
overlay = cv2.imread('samples/ryan_transparent.png', cv2.IMREAD_UNCHANGED)

# overlay function
def overlay_transparent(background_img, img_to_overlay_t, x, y, overlay_size=None):
    bg_img = background_img.copy()
    # convert 3 channels to 4 channels
    if bg_img.shape[2] == 3:
        bg_img = cv2.cvtColor(bg_img, cv2.COLOR_BGR2BGRA)

    if overlay_size is not None:
        img_to_overlay_t = cv2.resize(img_to_overlay_t.copy(), overlay_size)

    b, g, r, a = cv2.split(img_to_overlay_t)

    mask = cv2.medianBlur(a, 5)

    h, w, _ = img_to_overlay_t.shape
    roi = bg_img[int(y-h/2):int(y+h/2), int(x-w/2):int(x+w/2)]

    # Adjust mask size to match roi size
    mask = mask[:roi.shape[0], :roi.shape[1]]

    img1_bg = cv2.bitwise_and(roi.copy(), roi.copy(), mask=cv2.bitwise_not(mask))
    img2_fg = cv2.bitwise_and(img_to_overlay_t, img_to_overlay_t, mask=mask)

    if img1_bg is not None and img2_fg is not None:
        bg_img[int(y-h/2):int(y+h/2), int(x-w/2):int(x+w/2)] = img1_bg + img2_fg

    # convert 4 channels to 4 channels
    bg_img = cv2.cvtColor(bg_img, cv2.COLOR_BGRA2BGR)

    return bg_img

face_roi = []
face_sizes = []

# Initialize result variable outside the loop
result = None

# loop
while True:
    # read frame buffer from video
    ret, img = cap.read()
    if not ret:
        break

    # resize frame
    img = cv2.resize(img, (int(img.shape[1] * scaler), int(img.shape[0] * scaler)))
    ori = img.copy()

    # find faces
    if len(face_roi) == 0:
        faces = detector(img, 1)
    else:
        roi_img = img[face_roi[0]:face_roi[1], face_roi[2]:face_roi[3]]
        faces = detector(roi_img)

    # no faces
    if len(faces) == 0:
        print('no faces!')
        # Reset face_roi if no faces are found
        face_roi = []

    # find facial landmarks
    for face in faces:
        if len(face_roi) == 0:
            dlib_shape = predictor(img, face)
            shape_2d = np.array([[p.x, p.y] for p in dlib_shape.parts()])
        else:
            # Move the definition of roi_img here
            roi_img = img[face_roi[0]:face_roi[1], face_roi[2]:face_roi[3]]
            dlib_shape = predictor(roi_img, face)
            shape_2d = np.array([[p.x + face_roi[2], p.y + face_roi[0]] for p in dlib_shape.parts()])

        for s in shape_2d:
            cv2.circle(img, center=tuple(s), radius=1, color=(255, 255, 255), thickness=2, lineType=cv2.LINE_AA)

        # compute face center
        center_x, center_y = np.mean(shape_2d, axis=0).astype(int) # np.int

        # compute face boundaries
        min_coords = np.min(shape_2d, axis=0)
        max_coords = np.max(shape_2d, axis=0)

        # draw min, max coords
        cv2.circle(img, center=tuple(min_coords), radius=1, color=(255, 0, 0), thickness=2, lineType=cv2.LINE_AA)
        cv2.circle(img, center=tuple(max_coords), radius=1, color=(255, 0, 0), thickness=2, lineType=cv2.LINE_AA)

        # compute face size
        face_size = max(max_coords - min_coords)
        face_sizes.append(face_size)
        if len(face_sizes) > 10:
            del face_sizes[0]
        mean_face_size = int(np.mean(face_sizes) * 1.8)

        # compute face roi
        face_roi = np.array([int(min_coords[1] - face_size / 2), int(max_coords[1] + face_size / 2), int(min_coords[0] - face_size / 2), int(max_coords[0] + face_size / 2)])
        face_roi = np.clip(face_roi, 0, 10000)

        # draw overlay on face
        result = overlay_transparent(ori, overlay, center_x + 8, center_y - 25, overlay_size=(mean_face_size, mean_face_size))

    # visualize
    cv2.imshow('original', ori)
    cv2.imshow('facial landmarks', img)
    if result is not None:  # Check if result is defined before showing it
        cv2.imshow('result', result)
    if cv2.waitKey(1) == ord('q'):
        sys.exit(1)
