import os
import cv2
import time
import json
import torch
import base64
import asyncio
import datetime
from PIL import Image
from surrealdb import Surreal
from torchvision import datasets
from torch.utils.data import DataLoader
from facenet_pytorch import MTCNN, InceptionResnetV1

async def main_post(data, dbname):
    print('dbname:', dbname, '\n', data)
    async with Surreal("ws://localhost:8000/rpc") as db:
        await db.signin({"user": "admin", "pass": "password"})
        await db.use('FaceAttendanceDB', 'FaceAttendanceDB')
        await db.select(dbname)
        await db.create(
            dbname,
            data,
        )

def collate_fn(x):
    return x[0]

def faceRcognition(rtsp, classfloder):
    # initializing MTCNN and InceptionResnetV1 
    mtcnn0 = MTCNN(image_size=240, margin=0, keep_all=False, min_face_size=40) # keep_all=False
    mtcnn = MTCNN(image_size=240, margin=0, keep_all=True, min_face_size=40) # keep_all=True
    resnet = InceptionResnetV1(pretrained='vggface2').eval() 

    dataset = datasets.ImageFolder(os.path.join(os.path.abspath(os.getcwd()),'StuData',str(classfloder)))
    idx_to_class = {i:c for c,i in dataset.class_to_idx.items()} # accessing names of peoples from folder names
    loader = DataLoader(dataset, collate_fn=collate_fn)

    name_list = [] # list of names corrospoing to cropped photos
    embedding_list = [] # list of embeding matrix after conversion from cropped faces to embedding matrix using resnet

    for img, idx in loader:
        face, prob = mtcnn0(img, return_prob=True) 
        if face is not None and prob>0.92:
            emb = resnet(face.unsqueeze(0)) 
            embedding_list.append(emb.detach()) 
            name_list.append(idx_to_class[idx])   
                
    # saving data.pt file
    data = [embedding_list, name_list] 
    torch.save(data, 'data.pt') 

    # loading data.pt file
    load_data = torch.load('data.pt') 
    embedding_list = load_data[0] 
    name_list = load_data[1] 
    # print('name_list:::::', name_list) #All names in StuData inner folder of face image
    attendance_dbname = 'studentsAttendance'
    now = datetime.datetime.now()
    attendance = []
    response_list = {}
    
    cam = cv2.VideoCapture(rtsp) 
    
    classpath =  os.path.join(os.path.abspath(os.getcwd()), 'Pstudents', str(classfloder), now.strftime("%d%m%Y"))
    path =  os.path.join(os.path.abspath(os.getcwd()), 'Astudents', str(classfloder), now.strftime("%d%m%Y"))
    try:
        print('Make folder')
        os.makedirs(classpath)
        os.makedirs(path)
    except OSError as e:
        pass
    print('entering while loop')
    c = 0
    while True:
        ret, frame = cam.read()
        print('ret::::', ret)
        if not ret:
            print("fail to grab frame, try again")
            break
        img = Image.fromarray(frame)
        img_cropped_list, prob_list = mtcnn(img, return_prob=True) 
        
        if img_cropped_list is not None:
            print('img_cropped_list is not none', len(img_cropped_list))
            boxes, _ = mtcnn.detect(img)
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            
            for i, prob in enumerate(prob_list):
                if prob > 0.90:
                    print('prob_list:', prob)
                    emb = resnet(img_cropped_list[i].unsqueeze(0)).detach()
                    dist_list = [] # list of matched distances, minimum distance is used to identify the person
                    
                    for idx, emb_db in enumerate(embedding_list):
                        dist = torch.dist(emb, emb_db).item()
                        dist_list.append(dist)
                        
                    min_dist = min(dist_list) # get minumum dist value
                    min_dist_idx = dist_list.index(min_dist) # get minumum dist index
                    name = name_list[min_dist_idx] # get name corrosponding to minimum dist
                    box = boxes[i] 
                    crop = frame[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
                    try:
                        if min_dist<0.90:
                            if name in attendance:
                                continue
                            else:
                                attendance.append(name)
                                print('cropping time:', dt_string)
                                saved_img = os.path.join(classpath, name+'_'+str(c)+'_'+now.strftime("%d%m%Y_%H%M%S")+'.jpg')
                                cv2.imwrite(saved_img, crop)
                                data = {
                                    "name": name,
                                    "attendance": [1, now.strftime("%d/%m/%Y %H:%M:%S")],
                                    "year_id": now.strftime("%Y"),
                                    "img": saved_img
                                }
                                json_object = eval(json.dumps(data, indent = 4))
                                asyncio.run(main_post(json_object, attendance_dbname))
                            
                                jpg_img = cv2.imencode('.jpg', crop)
                                b64_string = base64.b64encode(jpg_img[1]).decode('utf-8')
                                data = {'Student name': name,
                                        'class name': classfloder,
                                        'attendance_status': 1,
                                        'Time Stamp': now.strftime("%d/%m/%Y %H:%M:%S"),
                                        'year_id': now.strftime("%Y"),
                                        'Base64 image': b64_string
                                        }
                                resp = eval(json.dumps(data, indent = 4))
                                response_list[name] = resp
                        else:
                            saved_img = os.path.join(path, 'Unknown_'+str(c)+'_'+now.strftime("%d%m%Y_%H%M%S")+'.jpg')
                            print('saved_img:', saved_img)
                            cv2.imwrite(saved_img, crop)
                            c += 1
                    except Exception as e:
                        print('Detect file e:', e)
                        pass  
    print('returned response_list///////////////')
    return response_list