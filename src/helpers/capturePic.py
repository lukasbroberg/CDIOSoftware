import cv2 as cv
 
cap = cv.VideoCapture(1)
ret, frame = cap.read()
cap.release()
 
if ret:
    cv.imwrite("capture5.png", frame)
    print("Saved capture.png")
else:
    print("Failed to capture image")