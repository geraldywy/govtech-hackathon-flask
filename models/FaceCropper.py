import cv2
from PIL import Image
from .base.ModelBaseClass import ModelBaseClass

class FaceCropper(ModelBaseClass):
    
    def __init__(self, object_key):

        self.model_name = "Face Cropper"

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.face_cascade = face_cascade
        self.object_key = object_key

    def generate(self, show_result=False):
        img = cv2.imread(self.object_key)
        if (img is None):
            print("Can't open image file")
            return 0
    
        faces = self.face_cascade.detectMultiScale(img, 1.1, 3, minSize=(100, 100))
        if (faces is None):
            print('Failed to detect face')
            return 0

        if (show_result):
            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x,y), (x+w, y+h), (255,0,0), 2)

        # facecnt = len(faces)
        # print("Detected faces: %d" % facecnt)
        height, width = img.shape[:2]
        # print("[height, width] -", (height, width))

        for (x, y, w, h) in faces:
            # print("detected [x,y,w,h] - ", x,y,w,h)

            # x is width, y is height
            y_offset_bottom = int((h) * 0.6)
            y_offset_top = int((h) * 0.7)
            x_offset = int((w) * 0.5) # equal for left and right
            y1 = max(0,y - y_offset_top)
            y2 = min(y + h + y_offset_bottom, height)
            x1 = max(0, x - x_offset)
            x2 = min(x + w + x_offset, width)
            
            # print("[cropped coord] - ", y1,y2,x1,x2)
            faceimg = img[y1:y2, x1:x2]
            final = cv2.cvtColor(faceimg, cv2.COLOR_BGR2RGB)
            
            data = Image.fromarray(final) 
            # saving the final output by overwriting
            data.save(self.object_key)