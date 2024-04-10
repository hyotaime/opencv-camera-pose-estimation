import numpy as np
import cv2 as cv

# The given video and calibration data
input_file = './test_video.mov'
K = np.array([[1.63243490e+03, 0, 7.29840790e+02],
              [0, 1.63197867e+03, 5.41535124e+02],
              [0, 0, 1]])

dist_coeff = np.array([2.74755274e-01, -1.23648857e+00, 6.93900545e-04, 2.07391502e-03, 1.84649263e+00])
board_pattern = (9, 6)
board_cellsize = 0.028
board_criteria = cv.CALIB_CB_ADAPTIVE_THRESH + cv.CALIB_CB_NORMALIZE_IMAGE + cv.CALIB_CB_FAST_CHECK

# Open a video
video = cv.VideoCapture(input_file)
assert video.isOpened(), 'Cannot read the given input, ' + input_file

fourcc = cv.VideoWriter.fourcc(*'mp4v')
out = cv.VideoWriter('pose_estimation_h.mp4', fourcc, 20.0, (int(video.get(3)), int(video.get(4))))

# Prepare a 3D box for simple AR
h_lower = board_cellsize * np.array(
    [[5, 0, 0], [6, 0, 0], [6, 5, 0], [5, 5, 0], [5, 3, 0], [3, 3, 0], [3, 5, 0], [2, 5, 0], [2, 0, 0], [3, 0, 0],
     [3, 2, 0], [5, 2, 0]])
h_upper = board_cellsize * np.array(
    [[5, 0, -1], [6, 0, -1], [6, 5, -1], [5, 5, -1], [5, 3, -1], [3, 3, -1], [3, 5, -1], [2, 5, -1], [2, 0, -1],
     [3, 0, -1], [3, 2, -1], [5, 2, -1]])

# Prepare 3D points on a chessboard
obj_points = board_cellsize * np.array([[c, r, 0] for r in range(board_pattern[1]) for c in range(board_pattern[0])])

# Run pose estimation
while True:
    # Read an image from the video
    valid, img = video.read()
    if not valid:
        break

    # Estimate the camera pose
    complete, img_points = cv.findChessboardCorners(img, board_pattern, board_criteria)
    if complete:
        ret, rvec, tvec = cv.solvePnP(obj_points, img_points, K, dist_coeff)

        # Draw the box on the image
        line_lower, _ = cv.projectPoints(h_lower, rvec, tvec, K, dist_coeff)
        line_upper, _ = cv.projectPoints(h_upper, rvec, tvec, K, dist_coeff)
        cv.polylines(img, [np.int32(line_lower)], True, (255, 0, 0), 2)
        cv.polylines(img, [np.int32(line_upper)], True, (0, 0, 255), 2)
        for b, t in zip(line_lower, line_upper):
            cv.line(img, np.int32(b.flatten()), np.int32(t.flatten()), (0, 255, 0), 2)

        # Print the camera position
        R, _ = cv.Rodrigues(rvec)  # Alternative) scipy.spatial.transform.Rotation
        p = (-R.T @ tvec).flatten()
        info = f'XYZ: [{p[0]:.3f} {p[1]:.3f} {p[2]:.3f}]'
        cv.putText(img, info, (10, 25), cv.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 0))

    # Show the image and process the key event
    out.write(img)
    cv.imshow('Pose Estimation (Chessboard)', img)
    key = cv.waitKey(10)
    if key == ord(' '):
        key = cv.waitKey()
    if key == 27:  # ESC
        break

video.release()
cv.destroyAllWindows()
