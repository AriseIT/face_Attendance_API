
import os
import cv2
import csv
import numpy as np
from datetime import datetime
import face_recognition as fr
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name("ariseit-face-attendance-aa6f0bedf315.json", scopes)
file = gspread.authorize(credentials) 
sheet = file.open("Daily Attendance").get_worksheet(0)

directory = ['Pstudents','Astudents']

for d in directory:
    try:
        os.mkdir(d)
    except Exception as e:
        print('Existing')
        pass

'''
rtsp://admin:admin@192.168.1.102:554/ch1/stream1
rtsp://admin:Password$133@192.168.1.64/Streaming/Channels/101
rtsp://admin:@192.168.1.15:554/ch0_0.264
'''

c = 0
known_names = []
known_name_encodings = []

path = ".\\train\\"
images = os.listdir(path)

for _ in images:
    image = fr.load_image_file(path + _)
    image_path = path + _
    encoding = fr.face_encodings(image)[0]
    known_name_encodings.append(encoding)
    known_names.append(os.path.splitext(os.path.basename(image_path))[0].capitalize())

cap = cv2.VideoCapture('D:\\Python\\arise\\A_code\\fireB_FcAt\\vid\\VID-20230524-WA0000.mp4')

while True:
    ret, image = cap.read()
    # image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    try:

        face_locations = fr.face_locations(image)
        face_encodings = fr.face_encodings(image, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = fr.compare_faces(known_name_encodings, face_encoding)
            name = ""
            face_distances = fr.face_distance(known_name_encodings, face_encoding)
            best_match = np.argmin(face_distances)
                        
            if matches[best_match]:
                name = known_names[best_match]
                print(name)

            crop = image[top:bottom, left:right]
            attandance = []

            if name != '': 
                ap = 'P'
                attandance.append(name)
                attandance.append(ap)
                print(c, ap)
                cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
                # cv2.rectangle(image, (left, bottom - 15), (right, bottom), (0, 255, 0), cv2.FILLED)
                # cv2.putText(image, name, (left + 6, bottom), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)
                # cv2.imwrite('img\\'+name+'.jpg', image)
                cv2.imwrite('Pstudents\\'+name+str(c)+'.jpg', crop)      
                
            else:
                ap = 'A'
                attandance.append('Unknown')
                attandance.append(ap)
                name = 'Unknown' 
                cv2.rectangle(image, (left, top), (right, bottom), (0, 0, 255), 2)
                # cv2.rectangle(image, (left, bottom - 15), (right, bottom), (0, 0, 255), cv2.FILLED)
                # cv2.putText(image, 'Unknown', (left + 6, bottom), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)
                # cv2.imwrite('img\\'+'Unknown.jpg', image)
                cv2.imwrite('Astudents\\'+'Unknown'+str(c)+'.jpg', crop)
            c += 1
            now = datetime.now()
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            
            l = len(sheet.col_values(1))
            l += 1
            sheet.update('A'+str(l),dt_string)
            print(l)
            sheet.update('B'+str(l),[attandance])
            
            fieldnames = ['Name', 'Class', 'Date', 'PA']
            with open('students.csv','a') as inFile:
                writer = csv.DictWriter(inFile, fieldnames=fieldnames)
                writer.writerow({'Name':name, 'Class':3, 'Date':dt_string, 'PA':ap})     # 'Id':ids, 
            print('attandance:', attandance)
            
    except Exception as e:
        print('end except:', e)
        
#     cv2.imshow("Result", image)
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break
# cap.release()
# cv2.destroyAllWindows()
