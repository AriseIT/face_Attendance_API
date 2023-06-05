import os
import cv2
import json
import glob
import threading
from app import app
from detect import *
from werkzeug.utils import secure_filename
from flask import Flask, flash, request, jsonify, redirect, render_template, Response

attendance_dbname = 'studentsAttendance'
stu_regist_db_name = 'registered_students'
camDevice_dbname = 'registered_camdevices'

directory = ['Pstudents','Astudents']
for d in directory:
	try:
		os.mkdir(d)
	except Exception as e:
		pass

#############
@app.route('/deletedb', methods=['POST'])
async def delDb():
	dbname = request.form.get('dbname')
	print('dbname:', dbname)
	async with Surreal("ws://localhost:8000/rpc") as db:
		await db.signin({"user": "admin", "pass": "password"})
		await db.use(dbname, dbname)
		await db.select(dbname)
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
	stu_img = request.files['image']
	print("fie>>>>>>>>>>>", stu_img)

	if request.method == "POST":
		if 'image' not in request.files:
			print('request:::', request.files)
			resp = jsonify({'message' : 'No file part in the request'})
			resp.status_code = 400
			return resp
		if stu_img.filename == '':
			print('file.filename:::', stu_img.filename)
			resp = jsonify({'message' : 'No file selected for uploading'})
			resp.status_code = 400
			return resp
		if stu_img:
			data = request.form.get('json')
			name_folder = request.form.get('folder')
			print("file name =====================", stu_img.filename)
			try:
				os.mkdir(os.path.join(app.config['UPLOAD_FOLDER'],name_folder))
			except OSError as err:
				print(err)
				pass
			imgpath = secure_filename(stu_img.filename)
			path = os.path.join(app.config['UPLOAD_FOLDER'],name_folder, imgpath)
			print('path:', path)
			stu_img.save(path)

			dbjson_object = eval(data)               
			asyncio.run(main_post(dbjson_object, stu_regist_db_name))

			resp = jsonify({"filename": stu_img.filename,"Student Data": dbjson_object, "Status":200})
			resp.status_code = 200
			return resp

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
    asyncio.run(main_post(dbjson_object, dbname))
    return jsonify(data)

@app.route('/StudentScalup', methods=['POST'])
def StudentScalup():
    data = request.json
    dbname = 'student_scalup'
    dbjson_object = eval(json.dumps(data, indent = 4))
    asyncio.run(main_post(dbjson_object, dbname))
    return jsonify(data)

# import required libraries
# import uvicorn
# from vidgear.gears.asyncio import WebGear_RTC

# # various performance tweaks
# options = {
#     "frame_size_reduction": 30,
# }
# # initialize WebGear_RTC app
# web = WebGear_RTC(source="edited.mp4", logging=True, **options)

# # run this app on Uvicorn server at address http://localhost:8000/
# uvicorn.run(web(), host="localhost", port=8000)

# # close app safely
# web.shutdown()

def previewcam(previewname, camid):
	print('in func previewcam//////////')
	cv2.namedWindow(previewname)
	cam = cv2.VideoCapture(camid)
	
	if cam.isOpened():
		rval, frame = cam.read()
	else:
		rval = False
	print('cammmmmmmmm', cam.isOpened(), rval)
	if cam.isOpened()==False and rval==False:
		return redirect('/')
	while rval:
		print('in loop;', rval)
		cv2.imshow(previewname, frame)
		rval, frame = cam.read()
		key = cv2.waitKey(20)
		if key == 27:  # Press ESC to exit
			break
	return cv2.destroyWindow(previewname)
 
@app.route('/livestream', methods=['GET'])
def stream():
	if request.method == 'GET':
		link = request.form.get('link')
		print('link:', link)

		class CamThread(threading.Thread):

			def __init__(self, previewname, camid):
				threading.Thread.__init__(self)
				self.previewname = previewname
				self.camid = camid

			def run(self):
				print("Starting " + self.previewname)
				return previewcam(self.previewname, self.camid)

		thread1 = CamThread("class", link)
		thread1.start()
	return 

# Get Student Registration
@app.route('/getStudentData', methods=['GET'])
async def getStu():
	if request.method == 'GET':
		dbquery = "SELECT * FROM "+ stu_regist_db_name
		try:
			fetch = (await getData(stu_regist_db_name, dbquery))[0].get('result')
			print('Surrealdb fetch:',fetch) #, await getData(stu_regist_db_name, dbquery))
			return fetch
		except Exception as e:
			print('getStudentData e>>>', e)
			return redirect('/')

# Get Division 
@app.route('/getDivisionData', methods=['GET'])
async def getDiv():
	if request.method == 'GET':
		div = request.form.get('divisionName')
		print('div::', div)
		dbquery = 'SELECT division FROM '+ stu_regist_db_name  
		try:
			fetch = (await getData(stu_regist_db_name, dbquery))[0].get('result')
			print('Surrealdb fetch:', fetch)
			return fetch
		except Exception as e:
			print('getdivdata e>>>', e)
			return redirect('/')

# Get Class
@app.route('/getClassData', methods=['GET'])
async def getCls():
	if request.method == 'GET':
		cls = request.form.get('className')
		print('cls::', cls)
		dbquery = "SELECT class FROM "+ stu_regist_db_name
		try:
			fetch = (await getData(stu_regist_db_name, dbquery))[0].get('result')
			print('Surrealdb fetch:', fetch)
			return fetch
		except Exception as e:
			print('getdivdata e>>>', e)
			return redirect('/')


# Get Device Registration
@app.route('/getCamData', methods=['GET'])
async def getCam():
	if request.method == 'GET':
		cam = request.form.get('device_name')
		rtsp = request.form.get('device_url')
		status = request.form.get('device_status')
		print('Device data:', cam, rtsp, status)

		dbquery = "SELECT * FROM "+ camDevice_dbname
		try:
			fetch = (await getData(camDevice_dbname, dbquery))[0].get('result')
			print('Surrealdb fetch:', fetch)
			return fetch
		except Exception as e:
			print('getCamData e>>>', e)
			return redirect('/')

# Get login 
@app.route('/getLoginData', methods=['GET'])
async def getLogin():
	if request.method == 'GET':
		user = request.form.get('userName')
		paword = request.form.get('password')
		schid = request.form.get('school_id')
		print('cam::', user, paword, schid)
		resp = jsonify({"user": user,"password": paword, "school_id":schid})
		resp.status_code = 200
		return resp

# Get Year
@app.route('/getAcedemicYear', methods=['GET'])
async def getAyear():
	if request.method == 'GET':
		dbquery = "SELECT year_id FROM "+ attendance_dbname
		try:
			fetch = (await getData(attendance_dbname, dbquery))[0].get('result')
			print('Surrealdb fetch:', fetch)
			return fetch[0]
		except Exception as e:
			print('getCamData e>>>', e)
			return redirect('/')

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
##################
@app.route('/getAttend', methods=['GET'])
async def getAtt():
	if request.method == 'GET':
		dbquery = "SELECT * FROM "+ attendance_dbname
		try:
			fetch = (await getData(attendance_dbname, dbquery))[0].get('result')
			print('Surrealdb fetch:', fetch)
			return fetch
		except Exception as e:
			print('getCamData e>>>', e)
			return redirect('/')
##########################

# Students Attendance mark an upload in db, face recognition using pyTorch 
@app.route('/StudentAttendance', methods=['POST'])
def Student_Attendance():
	if request.method == "POST":
		rtsp = request.form.get('device_url')
		classfloder = request.form.get('class folder')
		print("rtsp =====================", classfloder, rtsp)	
		response_list = faceRcognition(rtsp, classfloder)
		print('Student_Attendance:::', response_list)
		return response_list
    
if __name__ == "__main__":
    app.run()
