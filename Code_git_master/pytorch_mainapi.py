import os
import cv2
import json
from app import app
from detect import *
from flask import Flask, request, jsonify, redirect, Response

schoolRegistr_dbname = 'registered_school'
stu_regist_db_name = 'registered_students'
camDevice_dbname = 'registered_camdevices'
attendance_dbname = 'studentsAttendance'
stu_scalup_dbname = 'student_scalup'
schooldb = "schoolLogin_db"

master_filename = 'masters_data.json'
class_master_file = 'master_class_data.json'
division_master_file = 'master_division_data.json'

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
		await db.delete(dbname)
		resp = jsonify({"message": "Deleted successfully", "Data": "NULL", "Status code": 200})
		resp.status_code = 200
		return resp 


@app.route('/schoolLogin', methods=['POST']) 
def schoolLogin():
	if request.method == 'POST':
		user = request.form.get('json')
		print('login:::::::::::::', user)
		schooldb = "schoolLogin_db"
		dbjson_object = eval(user)               
		asyncio.run(main_post(dbjson_object, schooldb))
		resp = jsonify({"login data": dbjson_object, "Status":200})
		print("response schoolLogin data: \n",resp)
		resp.status_code = 200
		return resp

#####################

async def getData(dbname, dbquery):
	''' Get data from surrealDB by query '''

	async with Surreal("ws://localhost:8000/rpc") as db:
		await db.signin({"user": "admin", "pass": "password"})
		await db.use(dbname, dbname)
		await db.select(dbname)
		return await db.query(dbquery)

@app.errorhandler(404)
def not_found_error(error):
	resp = jsonify({"message": "API not found", "Data": "Null", "Status code": 404})
	resp.status_code = 404
	return resp

# ---------------------------------------------- API -----------------------------------------------
@app.route('/getLoginData', methods=['POST'])
async def getLogin():
	if request.method == 'POST':
		try:
			login = request.json
			print('login::', login)
			user_object = eval(json.dumps(login, indent = 4))
			dbquery = "SELECT * FROM "+ schooldb
			fetch = (await getData(schooldb, dbquery))[0].get('result')
			print('Surrealdb fetch:', fetch)
			user = user_object['username']
			paword = user_object['password']

			if user in fetch[0].values() and paword in fetch[0].values():
				print("Matched user")
				resp = jsonify({"message": "Success", "Data": fetch, "Status code": 200})
				resp.status_code = 200
				return resp
			else:
				print("None matched user")
				resp = jsonify({"message": "Username or password could Not find", "Data": "Null", "Status code": 400})
				resp.status_code = 400
				return resp

		except Exception as e:
			print('getCamData err>>>', e)
			resp = jsonify({"Message": "Not found", "Data": "Null", "Status code": 400})
			resp.status_code = 400
			return resp

@app.route('/StudentRegistration', methods=['POST'])
def Student_Registration():
	''' Student registration with face image file (any size), to train model save in local folder and data in DB '''
 
	if request.method == "POST":
		try:
			data = request.json
			print('StudentRegistration data length is: ', len(data))
			stu_object = eval(json.dumps(data, indent = 4))
			print('dbjson_object:', stu_object['student_data'])
			class_folder = stu_object['student_data']['class']
			name_folder = stu_object['student_data']['name']
			stu_img = stu_object['img']
				
			decodedData = base64.b64decode((stu_img))
			path = os.path.join(app.config['UPLOAD_FOLDER'],str(class_folder),name_folder)
			try:
				os.makedirs(path)
			except OSError as err:
				pass
			# Write Image from Base64 File
			imgFile = open(os.path.join(path,name_folder+'.jpg'), 'wb')
			imgFile.write(decodedData)
			imgFile.close()
			if os.path.join(path,name_folder+'.jpg') in os.listdir(path):
				# Create table for student registered data in the surrealDB
				asyncio.run(main_post(stu_object['student_data'], stu_regist_db_name))
    
				resp = jsonify({"Message": "Data Inserted Successfully", "Data": "Added", "Status code": 200})
				resp.status_code = 200
				return resp
			else:
				resp = jsonify({"Message": "Already exits", "Data": "Null", "Status code":208})
				resp.status_code = 208
				return resp
			
		except Exception as e:
			print('StudentRegistration err:', e)
			resp = jsonify({"Message": "Not found", "Data": "Null", "Status code": 400})
			resp.status_code = 400
			return resp

@app.route('/SchoolRegistration', methods=['POST'])
def school_registration():                                # need to be validate for already data exists in DB ----------?
	try:
		data = request.json
		dbjson_object = eval(json.dumps(data, indent = 4))
		print('data keys:', dbjson_object.keys())
		# School registration data stored in surrealDB
		asyncio.run(main_post(dbjson_object, schoolRegistr_dbname))
		resp = jsonify({"Message": "Data Inserted Successfully", "Data": "Added", "Status code": 200})
		resp.status_code = 200
		return resp
	except Exception as e:
		print('school_registration err:', e)
		resp = jsonify({"Message": "Not found", "Data": "Null", "Status code": 400})
		resp.status_code = 400
		return resp

@app.route('/DeviceRegistration', methods=['POST'])
def ipcam_registration():								 # need to be validate for already data exists in DB ----------?
	try:
		data = request.json
		dbjson_object = eval(json.dumps(data, indent = 4))
		asyncio.run(main_post(dbjson_object, camDevice_dbname))
		resp = jsonify({"Message": "Data Inserted Successfully", "Data": "Added", "Status code": 200})
		resp.status_code = 200
		return resp
	except Exception as e:
		print("DeviceREgister error: " + str(e))
		resp = jsonify({"Message": "Not found", "Data": "Null", "Status code": 400})
		resp.status_code = 400
		return resp

@app.route('/StudentScalup', methods=['POST'])
def StudentScalup():
	try:
		data = request.json
		dbjson_object = eval(json.dumps(data, indent = 4))
		asyncio.run(main_post(dbjson_object, stu_scalup_dbname))
		resp = jsonify({"Message": "Data Inserted Successfully", "Data": "Added", "Status code": 200})
		resp.status_code = 200
		return resp
	except Exception as e:
		print('Student scalup err:', e)
		resp = jsonify({"Message": "Not found", "Data": "Null", "Status code": 400})
		resp.status_code = 400
		return resp

# ''' Live streaming API '''
@app.route('/livestream/<path:rtsp>', methods=['GET', 'POST'])
def video_feed(rtsp):           
	print('rtsp link***********', rtsp)
	camera = cv2.VideoCapture(rtsp)
	while True:
		success, frame = camera.read()
		if not success:
			print('Camera on:',success)
			resp = jsonify({"Message": "Camera not found", "Data": "Null", "Status code": 400})
			resp.status_code = 400
			return resp
		else:
			return Response(gen_frames(rtsp), mimetype='multipart/x-mixed-replace; boundary=frame')
			# ret, buffer = cv2.imencode('.jpg', frame)
			# frame = buffer.tobytes()
			# return Response((b'--frame\r\n'
			# 					b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'),
			# 					mimetype='multipart/x-mixed-replace; boundary=frame')

    # async def...
	# if request.method == 'GET':
	# 	data = request.json
	# 	dbjson_object = eval(json.dumps(data, indent = 4))
	# 	print(dbjson_object['link'])
	# 	dbquery = "SELECT  * FROM "+ camDevice_dbname
	# 	fetch = (await getData(camDevice_dbname, dbquery))[0].get('result')
	# 	print('rtsp find:', fetch)
	# 	urls = []
	# 	for d in fetch:
	# 		urls.append(d['device_url'])
	# 	print('urls;;;;', urls)
	# 	if dbjson_object['link'] in urls:
	# 		link = dbjson_object['link'] #fetch[0]['device_url']
	# 		return Response(gen_frames(link), mimetype='multipart/x-mixed-replace; boundary=frame')
	# 	else:
	# 		resp = jsonify({"message": "Not found", "Data": "Null", "Status code": 400})
	# 		resp.status_code = 400
	# 		return resp
def gen_frames(link):
	camera = cv2.VideoCapture(link)
	while True:
		success, frame = camera.read()
		print('Camera on:',success)
		if not success:
			break
			yield success # redirect('/')
		else:
			ret, buffer = cv2.imencode('.jpg', frame)
			frame = buffer.tobytes()
			yield (b'--frame\r\n'
					b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

@app.route('/getStudentData', methods=['GET'])
async def getStu():
	if request.method == 'GET':
		try:
			dbquery = "SELECT * FROM "+ stu_regist_db_name
			fetch = (await getData(stu_regist_db_name, dbquery))[0].get('result')
			resp = jsonify({"message": "Success", "data": fetch, "Status code":201})
			resp.status_code = 201
			return resp
		except Exception as e:
			print('getStudentData err>>>', e)
			resp = jsonify({"message": "Not found", "Data": "Null", "Status code": 400})
			resp.status_code = 400
			return resp

@app.route('/getDivisionData', methods=['GET'])
def getDiv():
	if request.method == 'GET':
		try:
			with open(division_master_file) as file:
				file_contents = file.read()
			resp = jsonify({"message": "Success", "Data": eval(file_contents)['Division'], "Status code":201})
			resp.status_code = 201
			return resp
		except Exception as e:
			print('getDivisionData err>>>', e)
			resp = jsonify({"message": "No found division json file", "Data": "Null", "Status code":400})
			resp.status_code = 400
			return resp

@app.route('/getClassData', methods=['GET'])
def getCls():
	if request.method == 'GET':
		try: 
			with open(class_master_file) as file:
				file_contents = file.read()
			resp = jsonify({"message": "Success", "Data": eval(file_contents)['Class'], "Status code":201})
			resp.status_code = 201
			return resp
		except Exception as e:
			print('getClassData err>>>', e)
			resp = jsonify({"message": "No found class json file", "Status code":400})
			resp.status_code = 400
			return resp

@app.route('/getVibhagData', methods=['GET'])
def VibhagData():
	try:
		with open(master_filename) as file:
			file_contents = file.read()
		resp = jsonify({"message": "Success", "Data": eval(file_contents)['vibhag_details'], "Status code":201})
		resp.status_code = 201
		return resp
	except Exception as e:
		print('getVibhagData err>>>', e)
		resp = jsonify({"message": "May be not found masters json file", "Status code":400})
		resp.status_code = 400
		return resp

@app.route('/getBlockData', methods=['GET'])
def BlockData():
	try:
		with open(master_filename) as file:
			file_contents = file.read()
		resp = jsonify({"message": "Success", "Data": eval(file_contents)['block_details'], "Status code":201})
		resp.status_code = 201
		return resp
	except Exception as e:
		print('block_details err>>>', e)
		resp = jsonify({"message": "Not found masters json file", "Status code":400})
		resp.status_code = 400
		return resp

@app.route('/getDistrictData', methods=['GET'])
def DistrictData():
	try:
		with open(master_filename) as file:
			file_contents = file.read()
		resp = jsonify({"message": "Success", "Data": eval(file_contents)['district_details'], "Status code":201})
		resp.status_code = 201
		return resp
	except Exception as e:
		print('getDistrictData err>>>', e)
		resp = jsonify({"message": "Not found masters json file", "Status code":400})
		resp.status_code = 400
		return resp

@app.route('/getAcedemicYear', methods=['GET'])
async def getAyear():
	if request.method == 'GET':
		try:
			dbquery = "SELECT year_id FROM "+ attendance_dbname
			fetch = (await getData(attendance_dbname, dbquery))[0].get('result')
			print('Surrealdb fetch:', fetch[0])
			resp = jsonify({"message": "Success", "Data": fetch[0]['year_id'], "Status code": 201})
			resp.status_code = 201
			return resp
		except Exception as e:
			print('getCamData err>>>', e)
			resp = jsonify({"message": "Not Found", "Data": "Null", "Status code": 400})
			resp.status_code = 400
			return resp

@app.route('/getCamData', methods=['GET'])
async def getCam():
	if request.method == 'GET':
		try:
			dbquery = "SELECT * FROM "+ camDevice_dbname
			fetch = (await getData(camDevice_dbname, dbquery))[0].get('result')
			resp = jsonify({"message": "Success", "Data": fetch, "Status code": 201})
			resp.status_code = 201
			return resp
		except Exception as e:
			print('getCamData err>>>', e)
			resp = jsonify({"message": "Not Found", "Data": "Null", "Status code": 400})
			resp.status_code = 400
			return resp

@app.route('/StudentAttendance', methods=['POST'])
def Student_Attendance():
	'''Students Attendance mark an upload in db, face recognition using pyTorch'''
    
	if request.method == "POST":
		try:
			data = request.json
			rtsp_object = eval(json.dumps(data, indent = 4))
			print("Attendance=====================", rtsp_object)
			rtsp = rtsp_object['device_url']
			classfloder = rtsp_object['class name']
			try:
				response_list = faceRcognition(rtsp, classfloder)
				print('Student_Attendance:::', response_list)
    
				if response_list == {}:
					resp = jsonify({"message": "Camera may be off or no one student could recognised as known", "Data": "Null", "Status code": 400})
					resp.status_code = 400
					return resp
				return response_list
			except Exception as e:
				print('StudentAttendance error:', e)
				resp = jsonify({"message": "Not success", "Data": "Null", "Status code": 400})
				resp.status_code = 400
				return resp

		except Exception as e:
			print('Attendance err:', e)
			resp = jsonify({"message": "Not Found", "Data": "Null", "Status code": 400})
			resp.status_code = 400
			return resp

if __name__ == "__main__":
    app.run()
