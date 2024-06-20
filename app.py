from flask import Flask, request, jsonify, session, redirect, url_for, flash,send_file
from flask_mysqldb import MySQL
import bcrypt
import os
import cv2 as cv
import os
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from keras_facenet import FaceNet
import dlib
import csv
import pickle
import json
from flask_mail import Mail, Message
import uuid
import datetime
import random
import copy
from flask_sqlalchemy import SQLAlchemy
import ssl




embedder = FaceNet()

app = Flask(__name__)

app.secret_key = os.urandom(24)
# MySQL Configuration
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = '0000'
# app.config['MYSQL_DB'] = 'lost_people_finder'

# app.config['MYSQL_HOST'] = 'azure-finder-database.mysql.database.azure.com'
# app.config['MYSQL_USER'] = 'AbdulrahmanSaad'
# app.config['MYSQL_PASSWORD'] = 'finder66@@'
# app.config['MYSQL_DB'] = 'lost_people_finder'
# app.config['MYSQL_PORT'] = 3306  # Default MySQL port
# app.config['MYSQL_SSL_CA'] = '/DigiCertGlobalRootG2.crt.pem'
# app.config['MYSQL_SSL_VERIFY_CERT'] = True 

import mysql.connector
from mysql.connector import errorcode

# Obtain connection string information from the portal

config = {
  'host':'azure-finder-database.mysql.database.azure.com',
  'user':'AbdulrahmanSaad',
  'password':'finder66@@',
  'database':'lost_people_finder',
  'client_flags': [mysql.connector.ClientFlag.SSL],
  'ssl_ca': '/DigiCertGlobalRootG2.crt.pem'
}

# Construct connection string

try:
   mysql = mysql.connector.connect(**config)
   print("Connection established")
except mysql.connector.Error as err:
  if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
    print("Something is wrong with the user name or password")
  elif err.errno == errorcode.ER_BAD_DB_ERROR:
    print("Database does not exist")
  else:
    print(",llll")
else:
  cursor = mysql.cursor()







# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://AbdulrahmanSaad:finder66@@@azure-finder-database.mysql.database.azure.com/lost_people_finder'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask-Mail configurations
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Your email server
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'onlineshop500600@gmail.com'  # Your email address
app.config['MAIL_PASSWORD'] = 'lsnm gfag rawl tpqi'  # Your email password
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app) 
# mysql = MySQL(app)
# mysql = SQLAlchemy(app)

@app.route('/')
def home():
    cursor.execute("SELECT * FROM users;")
    rows = cursor.fetchall()
    
    print("Read",cursor.rowcount,"row(s) of data.")
    return "hello"

# User Registration
@app.route('/register', methods=['POST'])
def register():
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']
    phone_number=request.json['phone_number']
    cur = mysql.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    existing_user = cur.fetchone()
    if existing_user:
        return jsonify({'message': 'this email used before enter another email '})
    else :
        generate_code(email)
        return jsonify({'message': 'A verification code has been sent to your email.'})




def generate_code(email):
    cur = mysql.cursor()
    cur.execute("SELECT * FROM verification_codes WHERE email = %s", (email,))
    existing_user = cur.fetchone()
    if existing_user:
        cur.execute("DELETE FROM verification_codes WHERE email = %s", (email,))
        # Generate a verification code
    verification_code = generate_verification_code()
    # Store the verification code and email in the database
    cur = mysql.cursor()
    cur.execute("INSERT INTO verification_codes (email, code) VALUES (%s, %s)", (email, verification_code))
    mysql.commit()
    cur.close()
    # Send email with verification code
    msg = Message('Verification Code', sender='onlineshop500600@gmail.com', recipients=[email])
    msg.body = f"Your verification code is: {verification_code}"
    mail.send(msg)
    return redirect(url_for('verify_code'))

# User Login
@app.route('/login', methods=['POST'])
def login():
    email = request.json['email']
    password = request.json['password']

    cur = mysql.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    print(user[1])

    if user:
        if bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            session['logged_in'] = True
            cur.close()
            return jsonify({'message': 'Login successful'})
        else:
            cur.close()
            return jsonify({'message': 'Invalid email or password'})
    else:
        cur.close()
        return jsonify({'message': 'Invalid email or password'})

# User Logout
@app.route('/logout', methods=['POST'])
def logout():
    if 'logged_in' in session:
        session.pop('logged_in', None)
        return jsonify({'message': 'Logged out successfully'})
    else:
        return jsonify({'error': 'User not logged in'}), 401
    

def getClosetDistance(input_vector, results_map):
    embedder.metadata['distance_metric'] = 'euclidean'
    distances_map = {}

    for id, details in results_map.items():
        distance = embedder.compute_distance(input_vector, details['vector_image'])
        print(f"Distance between test img and {id} = {distance}")
        distances_map[id] = distance
 
    return sorted(distances_map.items(), key=lambda x: x[1])

def cropFaceFromImage(image):
        """
        Detect one face in the given image and crop it with a border.
        Return the cropped face with a suitable size for feeding to FaceNet Model.

        :param image_path: Path to the input image
        :return: Cropped face with suitable size if conditions are met
        """

        face_detector = dlib.get_frontal_face_detector()
        #nparr = np.frombuffer(img.read(), np.uint8)
        #image = cv.imdecode(nparr, cv.IMREAD_COLOR)
        # Check if the image was loaded successfully
        if image is None:
            raise FileNotFoundError("Error: Could not open or find the image.")

        # Convert the image to RGB (dlib expects RGB images)
        rgb_img =cv.cvtColor(image, cv.COLOR_BGR2RGB)

        # Detect faces in the image
        faces = face_detector(rgb_img)

        # Check if exactly one face was detected
        if len(faces) != 1:
            return None
        else :
        # Crop the face with a border
          x, y, w, h = faces[0].left(), faces[0].top(), faces[0].width(), faces[0].height()
          border = 10
          cropped_face = rgb_img[y-border:y+h+border, x-border:x+w+border]

        # Resize the cropped face to 160x160 pixels to make it suitable for FaceNet modeling
          resized_face = cv.resize(cropped_face, (160, 160))

        # Convert the cropped face to BGR format and add a border
          cropped_face_bgr = cv.cvtColor(cropped_face, cv.COLOR_RGB2BGR)
          border_color = (0, 255, 0)  # green border
          border_thickness = 5
          final_face = cv.copyMakeBorder(cropped_face_bgr, border_thickness, border_thickness, border_thickness, border_thickness, cv.BORDER_CONSTANT, value=border_color)
          return final_face


def get_embedding(face_img):
    face_img = face_img.astype('float32') # 3D(160x160x3)
    face_img = np.expand_dims(face_img, axis=0)
    # 4D (Nonex160x160x3)
    yhat= embedder.embeddings(face_img)
    return yhat[0] # 512D image (1x1x512)




@app.route('/lost', methods=['POST'])
def finder():
    # Get data from the request
   # data = request.json
    closed_dis = []
    person_name = request.form['person_name']
    age =request.form['age']
    date_of_lost =(request.form['date'])
    phone_number = request.form['phone_number']
    email = request.form['email']
    image = request.files['image']
    lng = request.form['lng']
    lat = request.form['lat']
    gender = request.form['gender']
   
    print("1")

    unique_filename = str(uuid.uuid4()) + os.path.splitext(image.filename)[-1]
    image.save( 'uploads/'+ unique_filename)
    imagef = cv.imread('uploads/'+ unique_filename) 
    croped= cropFaceFromImage(imagef)
    if croped is None:
      return jsonify({'error': 'Image does not contain exactly one face or No Face'})
    else :
         vector_image = get_embedding(croped)
         vector=pickle.dumps(vector_image)
         print("1")
     

   
    try:
        cursor = mysql.cursor()
        print("1")
        # Call the stored procedure
        #return jsonify({'Error_from_image': 'Image does not contain exactly one face or No Face'})
        cursor.callproc('search_in_find_people', (date_of_lost, age,gender))

        # Fetch all rows returned by the stored procedure
        rows = cursor.fetchall()
        print("1")
          
        # Convert rows to a list of dictionaries for JSON response
       
        if(len(rows)>0):
          results = {}
          final_result=[]
          for row in rows:
             result = {
                'person_name': row[1],
                'age': row[2],
                'date_of_lost': row[3],
                'phone_number': row[4],
                'email': row[5],
                'png_ref': row[6],
                'vector_image':pickle.loads(row[7]).tolist(),
                'lng': row[8],
                'lat': row[9],
                'gender':row[10]
             }
             results[row[0]]=result            
          closed_dis=getClosetDistance(vector_image,results)
          for id, distance in closed_dis:
              if(distance<=0.7):
                  final_result.append(results[id])
          if len(final_result)==0 :
             print("1")
             cursor = mysql.cursor()
             cursor.execute("INSERT INTO lost_people (person_name, age, date_of_lost,phone_number,email,vector_image,lng,lat,gender,png_ref) VALUES (%s, %s, %s,%s,%s, %s, %s,%s,%s,%s)", (person_name, age, date_of_lost,phone_number,email,vector,lng,lat,gender, 'uploads/'+ unique_filename))
             mysql.commit()
             cursor.close()
             return jsonify({'message': 'Person not found'})
         
                  
            
          else :
                 
               for item in final_result:
                  print("1")
                  image_path = item['png_ref']
                  item['image_url'] = f"http://192.168.1.19:5000/get_image/{image_path}"
                  del item['vector_image']

              
               return jsonify({'final_result': final_result})  
          

        else:
          print("1")
          cursor = mysql.cursor()
          cursor.execute("INSERT INTO lost_people (person_name, age, date_of_lost,phone_number,email,vector_image,lng,lat,gender,png_ref) VALUES (%s, %s, %s,%s,%s, %s, %s,%s,%s,%s)", (person_name, age, date_of_lost,phone_number,email,vector,lng,lat,gender, 'uploads/'+ unique_filename))
          mysql.commit()
          cursor.close()
          return jsonify({'message': 'Person not found'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
   

            
@app.route('/get_image/<path:image_path>')
def get_image1(image_path):
 
    return send_file(image_path, mimetype='image/png')


@app.route('/find', methods=['POST'])
def lost():
    try:
        print("1")
        # Get data from the request
        person_name = request.form['person_name']
        age = request.form['age']
        date_of_lost = request.form['date']
        phone_number = request.form['phone_number']
        email = request.form['email']
        image = request.files['image']
        lng = request.form['lng']
        lat = request.form['lat']
        gender = request.form['gender']
        print("2")
        # Save image and process
        unique_filename = str(uuid.uuid4()) + os.path.splitext(image.filename)[-1]
        image.save(os.path.join('uploads', unique_filename))
        imagef = cv.imread(os.path.join('uploads', unique_filename)) 
        cropped = cropFaceFromImage(imagef)
        print("3")
        if cropped is not None:
            vector_image = get_embedding(cropped)
            vector = pickle.dumps(vector_image)
        else:
            return jsonify({'error': 'Image does not contain exactly one face or No Face'})
        print("4")

        # Database operations
        cursor = mysql.cursor()
        cursor.callproc('search_in_lost_people', (date_of_lost, age, gender))
        rows = cursor.fetchall()
        print("5")

        if(len(rows)>0):
          results = {}
          final_result=[]
          for row in rows:
             result = {
                'person_name': row[1],
                'age': row[2],
                'date_of_lost': row[3],
                'phone_number': row[4],
                'email': row[5],
                'png_ref': row[6],
                'vector_image':pickle.loads(row[7]).tolist(),
                'lng': row[8],
                'lat': row[9],
                'gender':row[10]
             }
             results[row[0]]=result            
          closed_dis=getClosetDistance(vector_image,results)
          for id, distance in closed_dis:
              if(distance<=0.7):
                  final_result.append(results[id])
          if len(final_result)==0 :
                cursor.execute("INSERT INTO find_people (person_name, age, date_of_lost, phone_number, email, vector_image, lng, lat, gender, png_ref) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                               (person_name, age, date_of_lost, phone_number, email, vector, lng, lat, gender, 'uploads/' + unique_filename))
                mysql.commit()
                cursor.close()
                print("9")
                return jsonify({'message': 'Person not found'})
          else:
                for item in final_result:
                    image_path = item['png_ref']
                    item['image_url'] = f"http://192.168.1.19:5000/get_image/{image_path}"
                    del item['vector_image']
                print("10")

                return jsonify({'final_result': final_result})
        else:
            cursor.execute("INSERT INTO find_people (person_name, age, date_of_lost, phone_number, email, vector_image, lng, lat, gender, png_ref) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                           (person_name, age, date_of_lost, phone_number, email, vector, lng, lat, gender, 'uploads/' + unique_filename))
            mysql.commit()
            cursor.close()
            print("11")
            return jsonify({'message': 'Person not found'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/home_lost', methods=['Get'])
def H_lost():
    cur = mysql.cursor()
    cur.execute("SELECT * FROM lost_people ORDER BY id DESC LIMIT 5")
    rows = cur.fetchall()
        #return jsonify({'message': rows})
          
        # Convert rows to a list of dictionaries for JSON response
       
    if(len(rows)>0):
         
          results = {}
          final_result=[]
          for row in rows:
             result = {
                'person_name': row[1],
                'age': row[2],
                'date_of_lost': row[3],
                'phone_number': row[4],
                'email': row[5],
                'png_ref': row[6],
                'lng': row[8],
                'lat': row[9],
                'gender':row[10]
             }
             results[row[0]]=result
          for key, item in results.items():
    # Extract the image path from the item
             image_path = item['png_ref']
    # Construct the image URL and add it to the item
             item['image_url'] = f"http://192.168.1.19:5000/get_image/{image_path}"

    mysql.commit()
         
             
    return jsonify(results)    

@app.route('/home_find', methods=['Get'])
def H_find():
    cur = mysql.cursor()
    cur.execute("SELECT * FROM find_people ORDER BY id DESC LIMIT 5")
    rows = cur.fetchall()
        #return jsonify({'message': rows})
          
        # Convert rows to a list of dictionaries for JSON response
       
    if(len(rows)>0):
         
          results = {}
          final_result=[]
          for row in rows:
             result = {
                'person_name': row[1],
                'age': row[2],
                'date_of_lost': row[3],
                'phone_number': row[4],
                'email': row[5],
                'png_ref': row[6],
                'lng': row[8],
                'lat': row[9],
                'gender':row[10]
             }
             results[row[0]]=result
          for key, item in results.items():
    # Extract the image path from the item
            image_path = item['png_ref']

    # Construct the image URL and add it to the item
            item['image_url'] = f"http://192.168.1.19:5000/get_image/{image_path}"        
    return jsonify(results)  





@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        cur = mysql.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        if user:
         generate_code(email)
         return jsonify({'message': 'A verification code has been sent to your email.'})
        else:
            return jsonify({'message': 'Email address not found.'})


@app.route('/verify_reset_code_password', methods=['GET', 'POST'])
def verify_reset_code_password():
    entered_code = request.form['code']
    email = request.form['email']
    if verify(email, entered_code):
        if request.method == 'POST':
          return jsonify({'message': 'Correct code.'})
    else:
        return jsonify({'message': 'Incorrect code try again.'})

@app.route('/set_new_password', methods=['POST'])
def set_new_password():
    email = request.form['email']
    new_password = request.form['new_password']
    # Hash the new password
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    # Update the user's password in the database
    cur = mysql.cursor()
    cur.execute("UPDATE users SET password_hash = %s WHERE email = %s", (hashed_password, email))
    mysql.commit()
    cur.close()
    return jsonify({'message': 'Password has been reset successfully.'})
# Route for resetting password

def generate_verification_code():
    return str(random.randint(1000, 9999))



def verify(email, entered_code):
    cur = mysql.cursor()
    cur.execute("SELECT * FROM verification_codes WHERE email = %s", (email,))
    stored_code = cur.fetchone()
    #return jsonify({'message': 'stpred'})
    if stored_code:  # Check if any rows were returned
       
        stored_code = stored_code[2]  # Access the 'code' column from the returned row
        print(stored_code)
        print(entered_code)
        if stored_code == entered_code:
            return True
    return False

# Route for verifying the code
@app.route('/verify_code', methods=['POST'])
def verify_code():
    username =  request.form['username']
    password =  request.form['password']
    phone_number= request.form['phone_number']
    email = request.form['email']
    entered_code = request.form['code']
    print(phone_number)
    if verify(email, entered_code):
        # Perform actions for successful verification
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cur = mysql.cursor()
        cur.execute("INSERT INTO users (username, email, password_hash,phone_number) VALUES (%s, %s, %s,%s)", (username, email, hashed_password,phone_number))
        mysql.commit()
        cur.close()
        return jsonify({'message': 'User registered successfully'})
    else:
        return jsonify({'message': 'the code is not correct.'})
        # Handle failed verification
    




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)
