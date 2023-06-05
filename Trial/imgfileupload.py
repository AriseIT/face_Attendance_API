import os
import csv
import json
import random
import asyncio
import base64
from app import app
from surldb import main
from werkzeug.utils import secure_filename
from flask import Flask, flash, request, redirect, render_template

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def upload_form():
	return render_template('upload.html')

@app.route('/', methods=['POST'])
def upload_file(): 
	if request.method == 'POST':
		if 'file' not in request.files:
			flash('No file part')
			return redirect(request.url)
		file = request.files['file']
		if file.filename == '':
			flash('No file selected for uploading')
			return redirect(request.url)

		if file and allowed_file(file.filename):
			name = request.form.get('name')
			std = request.form.get('class')
			# ids = request.form.get('id')
			ids = ''.join(str(random.randint(0,9)) for x in range(6))
			fieldnames = ['Name', 'Class', 'ID']
			with open('students.csv','a') as inFile:
				writer = csv.DictWriter(inFile, fieldnames=fieldnames)
				writer.writerow({'Name': name, 'Class': std, 'ID':ids})
			
			# print('Data:::\n', data)
			print('filename:', file.filename.split('.')[0])
			stuid = file.filename.split('.')[0].replace(file.filename.split('.')[0], ids)
			path = str(stuid)+'.jpg'         
			print('path:', path)

			imgpath = secure_filename(path)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], imgpath))

			with open(os.path.join('Images', path), "rb") as image2string:
				converted_string = base64.b64encode(image2string.read())
   
			# data = (name, std, [0, "2023-05-23 08:05:05"],converted_string)
			data = {
                "name": name,
                "class": std,
                "attendance": [0, "2023-05-23 08:05:05"],
                "img": converted_string.decode()
            }
			json_object = json.dumps(data, indent = 4) 
			asyncio.run(main(json_object))

			with open('blobencode.bin', "wb") as file:
				file.write(converted_string)
    
			flash('File successfully uploaded')
			# imgUpload(path)
			return redirect('/')

		else:
			flash('Allowed file types are png, jpg, jpeg')
			return redirect(request.url)

		if request.method == 'GET':
			return render_template('upload.html')

if __name__ == "__main__":
    app.run()



##############################

@app.route('/schoolLogin', methods=['POST']) 
def schoolLogin():
	if request.method == 'POST':
		user = request.form.get('json')
		print('login::', user)
		schooldb = "schoolLogin_db"
		dbjson_object = eval(user)               
		asyncio.run(main_post(dbjson_object, schooldb))
		resp = jsonify({"login data": dbjson_object, "Status":200})
		print("response schoolLogin data: \n",resp)
		resp.status_code = 200
		return resp


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

##################
@app.route('/getAttend', methods=['GET'])
async def getAtt():
	if request.method == 'GET':
		dbquery = "SELECT * FROM "+ attendance_dbname
		try:
			fetch = (await getData(attendance_dbname, dbquery))[0].get('result')
			print('Surrealdb fetch:', fetch)
			resp = jsonify({"message": "Success", "Data": fetch, "Status":201})
			resp.status_code = 201
			return resp
		except Exception as e:
			print('getCamData e>>>', e)
			return redirect('/')
##########################
