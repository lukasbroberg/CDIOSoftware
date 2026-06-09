import cv2 as cv
 
cap = cv.VideoCapture(1)
ret, frame = cap.read()
cap.release()
 
if ret:
    cv.imwrite("test_image_aruco2.png", frame)
    print("Saved capture.png")
else:
    print("Failed to capture image")