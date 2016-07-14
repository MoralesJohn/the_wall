from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
from flask.ext.bcrypt import Bcrypt
import re
app = Flask(__name__)
app.secret_key = "slkdfjslakfjalskdja"
mysql = MySQLConnector(app,'wall_db')
bcrypt = Bcrypt(app)
email_regex = re.compile(r'^[a-zA-Z0-9\.\+_-]+@[a-zA-Z0-9\._-]+\.[a-zA-Z]*$')

@app.route("/")
def index():
	name = "friend"
	msg_data = ""
	cmnt_data = ""
	if "id" in session:
		query = "select first_name from users where id = :id"
		info = {"id": session["id"]}
		uid = mysql.query_db(query,info)
		name = uid[0]["first_name"]
		query = "select messages.id, message, messages.created_at, users.first_name, users.last_name from messages left join users on user_id = users.id order by messages.id desc"
		msg_data = mysql.query_db(query)
		query = "select comment, message_id, comments.created_at, users.first_name, users.last_name from comments left join messages on message_id = messages.id left join users on comments.user_id = users.id order by messages.id desc, comments.id asc"
		cmnt_data = mysql.query_db(query)
	return render_template("index.html", name = name, msg_data = msg_data, cmnt_data = cmnt_data)

@app.route("/logout")
def logout():
	session.pop("id")
	return redirect("/")

@app.route("/login")
def gateway():
	return render_template("login.html")

@app.route("/new", methods=["POST"])
def new_member():
	success = True
	data = request.form
	for key in data:
		if len(data[key]) < 1:
			success = False
			flash("<span class='alert'>All fields are required.</span>")
			break
	if (not data["first_name"].isalpha()) or (not data["last_name"].isalpha()):
		# no numerals
		success = False
		flash("<span class='alert'>No numerals allowed in the name fields.</span>")	
	if not email_regex.match(data["email"]):
		# verifying email addy
		success = False
		flash("<span class='alert'>Email invalid.</span>")
	if len(data["pw1"]) < 9:
		# no numerals
		success = False
		flash("<span class='alert'>Passwords must be a minimum of 9 characters.</span>")
	if data["pw1"] != data["pw2"]:
		# password and confirmation password match
		success = False
		flash("<span class='alert'>Passwords do not match.</span>")
	if not (any(chr.isdigit() for chr in data["pw1"])):
		# requires numeric
		success = False
		flash("<span class='alert'>Passwords must include a numeric character.</span>")
	if not (any(chr.isupper() for chr in data["pw1"])):
		# requires upper case letter
		success = False
		flash("<span class='alert'>Passwords must include an upper-case letter.</span>")
	if not success:
		return redirect("/login")
	pw_hash = bcrypt.generate_password_hash(data["pw1"])
	query = "insert into users (first_name, last_name, email, pw_hash, created_at, updated_at) values (:first_name, :last_name, :email, :pw_hash, NOW(), NOW())"
	info = {"first_name": data["first_name"], "last_name": data["last_name"], "email": data["email"], "pw_hash": pw_hash}
	mysql.query_db(query,info)
	query = "select id from users where email = :email"
	info = {"email": data["email"]}
	uid = mysql.query_db(query,info)
	session['id'] = uid[0]['id']
	return redirect('/')

@app.route("/member", methods=["POST"])
def member():
	data = request.form
	query = "select id, pw_hash from users where email = :email"
	info = {"email": data["email"]}
	uid = mysql.query_db(query,info)
	if bcrypt.check_password_hash(uid[0]["pw_hash"],data["password"]):
		session["id"] = uid[0]["id"]
	else:
		flash("User ID or password does not match.")
		return redirect("/login")
	return redirect("/")

@app.route("/message", methods=["POST"])
def add_message():
	data = request.form
	query = "insert into messages (user_id, message, created_at, updated_at) values (:uid, :message, NOW(), NOW())"
	info = {
		"uid": session["id"], 
		"message": data["msg_text"]
	}
	mysql.query_db(query,info)
	return redirect("/")

@app.route("/comment", methods=["POST"])
def add_comment():
	data = request.form
	query = "insert into comments (message_id, user_id, comment, created_at, updated_at) values (:msg_id, :uid, :comment, NOW(), NOW())"
	info = {
		"msg_id": data["msg_id"],
		"uid": session["id"], 
		"comment": data["cmnt_text"]
	}
	mysql.query_db(query,info)
	return redirect("/")

app.run(debug=True)
