from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
import os
import pymysql
import boto3

#DB Credentials to connect 
My_Access_Key = 'AKIAVKHJPTPCEBZCUSTN'
My_Secreat_Key = 'qdGZcNq6bOuz1erQNKLa5cOG1bh/q1v8r8f9Jq6/'
My_Region = 'us-east-1'

DB_Name = "defaultdb"
DB_user = "admin"
DB_Password = "multiweekdb"
DB_PORT = "3306"
DB_Endpoint = "multiweekdb.clnopyq3sfwe.us-east-1.rds.amazonaws.com"

app = Flask(__name__, static_folder='static')
app.secret_key = "my secret key"



@app.route('/', methods = ['GET', 'POST'])
def home():
    if request.method == 'POST':
        email = request.form['email']
        first_name = request.form['fn']
        last_name = request.form['ln']
        password = request.form['pass1']
        confirmpassword = request.form['pass2']
        if password != confirmpassword:
            return render_template("home.html", errors = "Both the passwords are not same")
        # elif ("." not in email) or ("@" not in email) or (".com") not in email:
        #     return render_template("home.html", errors = "Check the email format")
        else:
            try:
                print("hello")
                db_conn = pymysql.connect(host=DB_Endpoint, user=DB_user, password=DB_Password, database=DB_Name)
                db_cursor = db_conn.cursor()
                db_cursor.execute(
                    "INSERT INTO userdetailsKJUTURU(fn_user, ln_user, email_user, pass_user, confirm_user) VALUES (%s, %s, %s, %s, %s);",
                    (first_name, last_name, email, password, confirmpassword)
                )
                db_conn.commit()
                return render_template("thankyou.html")
            except Exception as e:
                print(e)
                return render_template("home.html", errors = "Email id already exists ")
    else:    
        return render_template("home.html")
    
@app.route('/login', methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db_conn = pymysql.connect(host=DB_Endpoint, user=DB_user, password=DB_Password, database=DB_Name)
        db_cursor = db_conn.cursor()
        query_result =  db_cursor.execute(
                    "SELECT pass_user FROM userdetailsKJUTURU WHERE email_user = %s", (email)
                )
        print(query_result)
        if query_result:
            db_password = db_cursor.fetchone()
            print(db_password)
            if password == db_password[0]:
                session['user'] = email
                return render_template("fileupload.html")   
            return render_template("login.html", error="Please Enter the Right Password. ")
        else:
            return render_template("login.html", error = "You don't have an account with us please signup")
    return render_template("login.html")

def file_billings(uploaded_file, logged_in_user):
    try:
        db_conn = pymysql.connect(host=DB_Endpoint, user=DB_user, password=DB_Password, database=DB_Name)
        db_cursor = db_conn.cursor()
        db_cursor.execute(
            "INSERT INTO billingtableKJUTURU(filename, email_user) VALUES (%s, %s);",
            (uploaded_file, logged_in_user)
            )
        db_conn.commit()
        return True
    except Exception as e:
        print (e)
        return False
    
my_sns_client = boto3.client('sns', aws_access_key_id=My_Access_Key, aws_secret_access_key=My_Secreat_Key, region_name=My_Region)
def sns_subscription(TopicARN, Protocol, EndPoint):
    subscription = my_sns_client.subscribe(TopicArn = TopicARN, Protocol=Protocol, Endpoint=EndPoint, ReturnSubscriptionArn=True)
    return subscription['SubscriptionArn']


@app.route('/filehandler', methods=['POST','GET'])
def file_and_email_handler():
    if request.method == 'POST':
        try:
            uploaded_file = request.files['formFileSm']
            uploaded_file_name = uploaded_file.filename
            my_bucket_client = boto3.client('s3', aws_access_key_id = My_Access_Key, aws_secret_access_key=My_Secreat_Key, region_name=My_Region)
            my_bucket_client.upload_fileobj(uploaded_file, "filehandlerbucket", uploaded_file_name)
            expiration_time = 4000
            my_bucket_file_url = my_bucket_client.generate_presigned_url('get_object', Params={'Bucket': 'filehandlerbucket', 'Key': uploaded_file_name}, ExpiresIn=expiration_time)
            print(my_bucket_file_url)
            notification_topic = my_sns_client.create_topic(Name="myTopic")
            user_email_address1 = request.form['InputEmail1']
            user_email_address2 = request.form['InputEmail2']
            user_email_address3 = request.form['InputEmail3']
            user_email_address4 = request.form['InputEmail4']
            user_email_address5 = request.form['InputEmail5']
            user = session['user']
            all_emails = [user_email_address1, user_email_address2, user_email_address3, user_email_address4, user_email_address5]
            for email in all_emails:
                if len(email) != 0:
                    topic_Arn = notification_topic['TopicArn']
                    protocol = 'email'
                    endpoint = email
                    response = sns_subscription(topic_Arn, protocol, endpoint)
                    my_sns_client.publish(TopicArn = topic_Arn, Subject = "Please Click on the below link to download.", Message = my_bucket_file_url)
            billing_result = file_billings(uploaded_file, session['user'])
            if billing_result == True:
                return render_template("fileupload.html", result = 'Upload to S3 Cloud Bucket Succesfully and A Mail was Set')
            if billing_result == False:
                return render_template("fileupload.html", error = 'Something Happened while uploading billing results.')
        except Exception as e:
            print(e)
            return render_template("fileupload.html", error = 'Something Went wrong while uploading file')

    else:
        return render_template("fileupload.html", error = 'Please upload the file')
    
@app.route('/billedfiles')
def billedfiles():
    billedfiles = {}
    db_conn = pymysql.connect(host=DB_Endpoint, user=DB_user, password=DB_Password, database=DB_Name)
    db_cursor = db_conn.cursor()
    query_result =  db_cursor.execute(
            "SELECT * FROM billingtableKJUTURU"
    )
    result = db_cursor.fetchall()
    for item in result:
        billedfiles[item[0]] = item[1]
    return render_template("billedfiles.html", billedfiles = billedfiles)


@app.before_request
def create_tables():
    try:
        connection = pymysql.connect(host=DB_Endpoint, user=DB_user, password=DB_Password, database=DB_Name)
        print("Connected to Database: ")
        cursor = connection.cursor()
        print("Creating Required Tables:  ")
        cursor.execute("USE defaultdb;")
        cursor.execute("CREATE TABLE userdetailsKJUTURU(fn_user varchar(50), ln_user varchar(50), email_user varchar(50) unique, pass_user varchar(50), confirm_user varchar(50), primary key(email_user))")
        print("Created Signup Table: ")
        cursor.execute("CREATE TABLE billingtableKJUTURU(filename varchar(50), email_user varchar(50))")
        print("Created Billing Table.....!")
        connection.commit()
        print("Both the tables are created succesfuly....!")
    except Exception as e:
        print("Something wrong happend while creating the tables.....")
        print(e)
        # return e

if __name__ == "__main__":
    app.run(debug=True)