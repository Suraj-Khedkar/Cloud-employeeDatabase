from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
import re
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('AddEmp.html')


@app.route("/about", methods=['POST'])
def about():
    return render_template('www.intellipaat.com')


@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)

@app.route("/getemp",methods=["GET","POST"])
def getemp():
    return render_template('GetEmp.html')

@app.route("/fetchdata", methods=["POST"])
def fetchdata():
    emp_id = request.form['emp_id']
    cursor = db_conn.cursor()
    sql_select = "SELECT * FROM `employee` WHERE `empid`=%s"
    try:
        cursor.execute(sql_select,(emp_id))
        result = cursor.fetchone()
        empid = result[0]
        fname = result[1]
        lname = result[2]
        interest = result[3]
        location = result[4]
        image_url =""
        try:
            emp_image_file_name_in_s3 = "emp-id-" + str(empid) + "_image_file"
            s3 = boto3.resource('s3')
            my_bucket=s3.Bucket(custombucket).objects.all()
            
            substring =  "\d"

            for obj in my_bucket.objects.all():
                if re.search(substring,  obj.key):  
                    print(obj.key)
        except Exception as e:
            return str(e)
    except Exception as e:
        return str(e)

    finally:
        cursor.close()
        return render_template('GetEmpOutput.html',empid=empid,fname=fname,lname=lname,interest=interest,location=location,image_url = image_url)
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
