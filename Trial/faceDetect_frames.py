import imutils
import time
import cv2
import os

detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

print("[INFO] starting video stream...")
cap = cv2.VideoCapture(r'.\\vid\\VID-20230524-WA0000.mp4', 0)
time.sleep(2.0)
total = 0

while True:
    ret, frame = cap.read()
    if ret == False: break
#     orig = frame.copy()
    frame = imutils.resize(frame, width=1000)
    rects = detector.detectMultiScale(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    for (x, y, w, h) in rects:
        crop = frame[x:w, h:y]
        try:
            p = os.path.sep.join(['.\\images\\', "{}.jpg".format(str(name))])
                
            cv2.imwrite('images\\stu'+str(c)+'.jpg', crop)
        except:
            pass
        #     p = os.path.sep.join(['.\\images\\', "{}.png".format(str(total).zfill(5))])
        #     cv2.imwrite(p, orig)
        #     total += 1
        #     cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

print("[INFO] {} face images stored".format(total))
cap.release()
print("[INFO] cleaning up...")
cv2.destroyAllWindows()
