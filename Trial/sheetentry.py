import os
import csv
import cv2
import json
import random
import asyncio
import base64
import datetime
from app import app
from surldb import main
import face_recognition as fr
from werkzeug.utils import secure_filename
from flask import Flask, flash, request, jsonify, redirect, render_template 


@app.route('/', methods=['POST'])
def upload_file(): 
    file = request.files['file']
    print("fie>>>>>>>>>>>", file)
    
    if request.method == "POST":
        if 'file' not in request.files:
            print('request:::', request.files)
            resp = jsonify({'message' : 'No file part in the request'})
            resp.status_code = 400
            return resp
        if file.filename == '':
            print('file.filename:::', file.filename)
            resp = jsonify({'message' : 'No file selected for uploading'})
            resp.status_code = 400
            return resp
        
        if file:
            print("file name =====================", file.filename)
            now_vid = datetime.datetime.now()
            dt_string_vid = now_vid.strftime("%d-%m-%Y_%H_%M_%S")
            filename = secure_filename(str(dt_string_vid)+".jpg")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            resp = jsonify({"filename": filename, "Status":200})
            print("resp!!!!!!!!!!!!!!!",resp)
            resp.status_code = 200
            
            print(filename)

            path = os.path.join(app.config['UPLOAD_FOLDER'],filename)
            print('path:', path)

            directory = ['Pstudents','Astudents']

            for d in directory:
                try:
                    os.mkdir(d)
                except Exception as e:
                    print('Existing')
                    pass
            
			# data = {
            #     "name": name,
            #     "class": std,
            #     "attendance": [0, "2023-05-23 08:05:05"],
            #     "img": path
            # }
            image = cv2.imread(path)
            up_width = 800
            up_height = 600
            up_points = (up_width, up_height)
            image = cv2.resize(image, up_points, interpolation= cv2.INTER_LINEAR)

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
                        # data = {
                        #     "name": name,
                        #     "class": std,
                        #     "attendance": [0, "2023-05-23 08:05:05"],
                        #     "img": path
                        # }
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
                    now = datetime.datetime.now()
                    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
                    
                    # l = len(sheet.col_values(1))
                    # l += 1
                    # sheet.update('A'+str(l),dt_string)
                    # print(l)
                    # sheet.update('B'+str(l),[attandance])
                    
                    fieldnames = ['Name', 'Class', 'Date', 'PA']
                    with open('students.csv','a') as inFile:
                        writer = csv.DictWriter(inFile, fieldnames=fieldnames)
                        writer.writerow({'Name':name, 'Class':3, 'Date':dt_string, 'PA':ap})     # 'Id':ids, 
                    print('attandance:', attandance)
                return resp
                                        
            except Exception as e:
                print('end except:', e)
                return e
                
            ''' data needed to generate'''
            # json_object = json.dumps(data, indent = 4)                  
            # asyncio.run(main(json_object))

        return resp
    return 'file'


if __name__ == "__main__":
    app.run()
