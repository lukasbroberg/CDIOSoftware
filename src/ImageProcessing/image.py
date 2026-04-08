import cv2 as cv

#Loads the image and returns image
def loadImage(imagePath):
    image = cv.imread(imagePath)
    if image is None:
        raise FileNotFoundError("Couldnt load image")
    return image