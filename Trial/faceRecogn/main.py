import os
import csv
import cv2
import json
import random
import imutils
import asyncio
import base64
import datetime
import threading
import numpy as np
from app import app
from surrealdb import Surreal
import face_recognition as fr
from werkzeug.utils import secure_filename
from flask import Flask, flash, request, jsonify, redirect, render_template, Response
		

known_names = []
known_name_encodings = []

trainpath = ".\\train\\"
images = os.listdir(trainpath)
directory = ['Pstudents','Astudents','train','StuData']

stu_regist_db_name = 'registered_students'
camDevice_dbname = 'registered_camdevices'
attendance_dbname = 'studentsAttendance'

for d in directory:
	try:
		os.mkdir(d)
	except Exception as e:
		pass


async def main_post(data, dbname):
    print('dbname:', dbname, '\n', data)
    async with Surreal("ws://localhost:8000/rpc") as db:
        await db.signin({"user": "admin", "pass": "password"})
        await db.use(dbname, dbname)
        await db.select(dbname)
        await db.create(
            dbname,
            data,
        )
        # await db.update(dbname, data)

#############
@app.route('/deletedb', methods=['POST'])
async def delDb():
	dbname = request.form.get('dbname')
	print('dbname:', dbname)
	async with Surreal("ws://localhost:8000/rpc") as db:
		await db.signin({"user": "admin", "pass": "password"})
		await db.use(dbname, dbname)
		await db.select(dbname)
		print(await db.delete(dbname))
		return (await db.delete(dbname))
#####################

async def getData(dbname, dbquery):
	async with Surreal("ws://localhost:8000/rpc") as db:
		await db.signin({"user": "admin", "pass": "password"})
		await db.use(dbname, dbname)
		await db.select(dbname)
		return await db.query(dbquery)

@app.route('/StudentRegistration', methods=['POST'])
def Student_Registration():
    data = request.json
    # print(data, type(data))
    dbjson_object = eval(json.dumps(data, indent = 4))                  
    print(type(dbjson_object))
    asyncio.run(main_post(dbjson_object, stu_regist_db_name))
    return jsonify(data)
     
@app.route('/DeviceRegistration', methods=['POST'])
def ipcam_registration():
    data = request.json
    dbjson_object = eval(json.dumps(data, indent = 4))
    asyncio.run(main_post(dbjson_object, camDevice_dbname))
    return jsonify(data)

@app.route('/SchoolRegistration', methods=['POST'])
def school_registration():
    data = request.json
    dbname = 'registered_school'
    dbjson_object = eval(json.dumps(data, indent = 4))
    print('dbjson_object:', dbjson_object)
    # data = json.load(open('data.json'))
    # for i in data['masters data']:
    #     print(i)
    asyncio.run(main_post(dbjson_object, dbname))
    return jsonify(data)

# http://localhost:5000/save_student_scalup
@app.route('/StudentScalup', methods=['POST'])
def StudentScalup():
    data = request.json
    dbname = 'student_scalup'
    dbjson_object = eval(json.dumps(data, indent = 4))
    asyncio.run(main_post(dbjson_object, dbname))
    return jsonify(data)

@app.route('/livestream', methods=['POST'])
def stream():
	if request.method == 'POST':
		
		link = request.form.get('link')
		print('link:', link)
  
		class CamThread(threading.Thread):

			def __init__(self, previewname, camid):
				threading.Thread.__init__(self)
				self.previewname = previewname
				self.camid = camid

			def run(self):
				print("Starting " + self.previewname)
				previewcam(self.previewname, self.camid)

		# Function to preview the camera.
		def previewcam(previewname, camid):
			print('in func previewcam//////////')
			cv2.namedWindow(previewname)
			cam = cv2.VideoCapture(camid)
			
			if cam.isOpened():
				rval, frame = cam.read()
			else:
				rval = False
			print(cam.isOpened(), rval)
			while rval:
				cv2.imshow(previewname, frame)
				rval, frame = cam.read()
				key = cv2.waitKey(20)
				if key == 27:  # Press ESC to exit/close each window.
					break
			cv2.destroyWindow(previewname)

		thread1 = CamThread("class", link)
		thread1.start()
		return redirect('/')

# Get Student Registration
@app.route('/getStudentData', methods=['GET'])
async def getStu():
	if request.method == 'GET':
		dbquery = "SELECT * FROM "+ stu_regist_db_name
		try:
			fetch = (await getData(stu_regist_db_name, dbquery))[0].get('result')
			print('Surrealdb fetch:',fetch) #, await getData(stu_regist_db_name, dbquery))
			return fetch[0]
		except Exception as e:
			print('getStudentData e>>>', e)
			return redirect('/')

  
@app.route('/getDivisionData', methods=['GET'])
async def getDiv():
	if request.method == 'GET':
		div = request.form.get('divisionName')
		print('div::', div)
		dbquery = 'SELECT * FROM '+ stu_regist_db_name +' WHERE division IS '+ str(div) 
		try:
			fetch = (await getData(stu_regist_db_name, dbquery))[0].get('result')
			print('Surrealdb fetch:', fetch)
			return fetch[0]
		except Exception as e:
			print('getdivdata e>>>', e)
			return redirect('/')


@app.route('/getClassData', methods=['GET'])
async def getCls():
	if request.method == 'GET':
		cls = request.form.get('className')
		print('cls::', cls)
		dbquery = "SELECT class FROM "+ stu_regist_db_name #+' WHERE class = '+ cls 
		try:
			fetch = (await getData(stu_regist_db_name, dbquery))[0].get('result')
			print('Surrealdb fetch:', fetch)
			return fetch[0]
		except Exception as e:
			print('getdivdata e>>>', e)
			return redirect('/')


# Get Device Registration
@app.route('/getCamData', methods=['GET'])
async def getCam():
	if request.method == 'GET':
		dbquery = "SELECT * FROM "+ camDevice_dbname  # WHERE class = 'class'") 
		try:
			fetch = (await getData(camDevice_dbname, dbquery))[0].get('result')
			print('Surrealdb fetch:', fetch)
			return fetch[0]
		except Exception as e:
			print('getCamData e>>>', e)
			return redirect('/')

@app.route('/getLoginData', methods=['GET'])
async def getLogin():
	if request.method == 'GET':
		cam = request.form.get('userName')
		paword = request.form.get('password')
		schid = request.form.get('school_id')
		print('cam::', cam, paword, schid)
		dbquery = "SELECT * FROM "+ stu_regist_db_name  # WHERE class = 'class'")     #[0]["result"]
		try:
			fetch = (await getData(stu_regist_db_name, dbquery))[0].get('result')
			print('Surrealdb fetch:',fetch) #, await getData(stu_regist_db_name, dbquery))
			return fetch[0]
		except Exception as e:
			print('getStudentData e>>>', e)
			return redirect('/')

@app.route('/getAcedemicYear', methods=['GET'])
async def getAyear():
	if request.method == 'GET':
		dbquery = "SELECT year_id FROM "+ attendance_dbname  # WHERE class = 'class'
		try:
			fetch = (await getData(attendance_dbname, dbquery))[0].get('result')
			print('Surrealdb fetch:', fetch)
			return fetch[0]
		except Exception as e:
			print('getCamData e>>>', e)
			return redirect('/')

##################
@app.route('/getAttend', methods=['GET'])
async def getAtt():
	if request.method == 'GET':
		dbquery = "SELECT * FROM "+ attendance_dbname  # WHERE class = 'class'
		try:
			fetch = (await getData(attendance_dbname, dbquery))[0].get('result')
			print('Surrealdb fetch:', fetch)
			return fetch
		except Exception as e:
			print('getCamData e>>>', e)
			return redirect('/')


detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

def face_detect(path, name):
	im = cv2.imread(path)
	frame = imutils.resize(im, width=1000)
	rects = detector.detectMultiScale(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
	for (x, y, w, h) in rects:
		crop = im[x:w, h:y]
		try:
			p = os.path.sep.join(['.\\StuData\\', "{}.jpg".format(str(name))])
			print('crop:::::', type(crop))
			cv2.imwrite(p, crop)
			yield (b'--frame\r\n'
				b'Content-Type: image/jpeg\r\n\r\n' + open(name+'.jpg', 'rb').read() + b'\r\n')
		except Exception as e:
			print('face_detect e>>>', e)
			return redirect('/')
			

@app.route('/StudentAttendance', methods=['POST'])
def Student_Attendance(): 
	file = request.files['file']
	print("fie>>>>>>>>>>>", file)
 
	for ime in images:
		image = fr.load_image_file(trainpath + ime)
		image_path = trainpath + ime
		encoding = fr.face_encodings(image)[0]
		known_name_encodings.append(encoding)
		known_names.append(os.path.splitext(os.path.basename(image_path))[0].capitalize())
  
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
			now = datetime.datetime.now()
			c = 0
			print("file name =====================", file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
			resp = jsonify({"filename": file.filename, "Status":200})
			print("resp!!!!!!!!!!!!!!!",resp)
			resp.status_code = 200
   
			path = os.path.join(app.config['UPLOAD_FOLDER'],file.filename)
			print('path:', path)
			image = cv2.imread(path)
			up_points = (1000, 600)
			image = cv2.resize(image, up_points, interpolation= cv2.INTER_LINEAR)
			face_locations = fr.face_locations(image)
			face_encodings = fr.face_encodings(image, face_locations)
			# print(face_encodings, face_locations)
			for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
				matches = fr.compare_faces(known_name_encodings, face_encoding)
				name = ""
				face_distances = fr.face_distance(known_name_encodings, face_encoding)
				best_match = np.argmin(face_distances)	
				if matches[best_match]:
					name = known_names[best_match]
					print(name)
     
				attandance = []
    
				crop = image[top:bottom, left:right]
				dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    
				if name != '':
					saved_img = '.\\Pstudents\\'+name+'_'+now.strftime("%d%m%Y_%H%M%S")+'.jpg'
					cv2.imwrite(saved_img, crop)
					ap = 1
					attandance.append(name)
					attandance.append(ap)
					cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
					data = {
						"name": name,
						# "roll no": ,
						"attendance": [ap, dt_string],
						"year_id": now.strftime("%Y"),
						"img": saved_img
					}
					json_object = eval(json.dumps(data, indent = 4))
					asyncio.run(main_post(json_object, attendance_dbname))
				else:
					saved_img = '.\\Astudents\\'+'Unknown'+now.strftime("%d%m%Y_%H%M%S")+'.jpg'
					cv2.imwrite(saved_img, crop)
					ap = 0
					attandance.append('Unknown')
					attandance.append(ap)
					name = 'Unknown' 
					print('attendance:', c, ap)
					cv2.rectangle(image, (left, top), (right, bottom), (0, 0, 255), 2)
					data = {
						"name": name,
						# "roll no": 
						"attendance": [ap, dt_string],
						"year_id": now.strftime("%Y"),
						"img": saved_img
					}
					json_object = eval(json.dumps(data, indent = 4))
					asyncio.run(main_post(json_object, attendance_dbname))

				c += 1
				cv2.imwrite(".\\StuData\\"+now.strftime("%d%m%Y_%H%M%S")+".jpg", image)
		return resp
	return 'file'


'''
@app.route('/getFaceimage', methods=['GET'])
def getcrop():
	if request.method == 'GET':
		try:     		#Get the latest image file in the given directory   
			classfloder = request.form.get('class name')
			now = datetime.datetime.now()
			paths = os.listdir(os.path.join(os.path.join(os.path.abspath(os.getcwd()),'Pstudents',classfloder,now.strftime("%d%m%Y"))))
			crop_img = [os.path.join(os.path.abspath(os.getcwd()),'Pstudents',classfloder,now.strftime("%d%m%Y"), basename) for basename in paths]
			print(max(crop_img, key=os.path.getctime))
			img = cv2.imread(max(crop_img, key=os.path.getctime))
			jpg_img = cv2.imencode('.jpg', img)
			b64_string = base64.b64encode(jpg_img[1]).decode('utf-8')
			tstamp, stuname = '', ''
			if '\\' in max(crop_img, key=os.path.getctime):
				strfind = ((max(crop_img, key=os.path.getctime).replace('\\', '.')).split(".")[-2]).split('_')
				tstamp = '_'.join(strfind[-2:])
				stuname = strfind[-3]
			elif '/' in max(crop_img, key=os.path.getctime):
				strfind = ((max(crop_img, key=os.path.getctime).replace('/', '.')).split(".")[-2]).split('_')
				tstamp = '_'.join(strfind[-2:])
				stuname = strfind[-3]
			# stuname = (max(crop_img, key=os.path.getctime).split(".")[-2]).split('_')[-2]
			print('data:::::::', tstamp, stuname)
			data = {'Time Stamp': tstamp,
					'Student name': stuname,
					'Base64 image': b64_string
					}
			resp = eval(json.dumps(data, indent = 4))
			return resp
		except Exception as e:
			print('getCamData e>>>', e)
			return redirect('/')
'''

if __name__ == "__main__":
    app.run()
