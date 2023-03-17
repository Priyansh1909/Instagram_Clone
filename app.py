from flask import Flask, render_template, request, redirect, flash, session, url_for, jsonify
from flask_session import Session
from flask_socketio import SocketIO, Namespace,emit,join_room
from werkzeug.utils import secure_filename
import mysql.connector
import os
import uuid as uuid

app = Flask(__name__)
app.secret_key = 'set some super secret key'
app.config['SECRET_KEY'] = "set some supper sceret key"
Socketio = SocketIO(app)


    

    
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024
abpath = os.getcwd() + "\static"
# print(abpath)
path = os.path.relpath(abpath)
# print("path :",path)


UPLOAD_FOLDER = os.path.join(path, "profile_pic")
# print(UPLOAD_FOLDER)
if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

UPLOAD_FOLDER_POST = os.path.join(path, "Posts")
# f
if not os.path.isdir(UPLOAD_FOLDER_POST):
    os.mkdir(UPLOAD_FOLDER_POST)

app.config["UPLOAD_FOLDER_POST"] = UPLOAD_FOLDER_POST

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app.config["SESSION_TYPE"] = "filesystem"
Session(app)
mydb = mysql.connector.connect(host= "localhost", user = "root", password = "password123", database = "instagram")
cursor = mydb.cursor()


sessionid = {}
message_unread = {}


#all Routes

# Login Auth
@app.route("/", methods=["POST","GET"])
def index():
    if "id" in session:
        return redirect("/home")
        
    elif request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Checking if Username exist in the database or not
        cursor.execute("SELECT * FROM `userid` WHERE `username` = '{}' ".format(username))
        usernamecheck = cursor.fetchall()
        print(usernamecheck)
    

        # checking if username and password match or not 
        # cursor.execute("SELECT * FROM `userid` WHERE `username` = '{}' AND `password` = '{}'".format(username,password))
        # check = cursor.fetchall()
        # print(check)

        if len(username) == 0 & len(password) == 0:
            flash("enter your username and password")

        elif len(username) == 0:
            flash("enter your username")
        
        elif len(password) == 0:
            flash("Enter your password")

        elif len(usernamecheck) == 0:
            flash("Username not found")
        
        elif password != usernamecheck[0][2]:
            flash("Incorrect Password")
        
        else:
            if username == usernamecheck[0][1] and password == usernamecheck[0][2]:
                print("WHAT ", session)
                session['id'] = usernamecheck[0][0]
                print(session)
                return redirect("/home")
            else:
                return redirect("/")


    return  render_template("index.html")

@app.route("/SignUp", methods=["POST", "GET"])
def SignUp():
    if request.method == "POST":
        email = request.form.get("email").lower()
        username = request.form.get("username").lower()
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        cursor.execute("SELECT * FROM `userid` WHERE `email` = '{}'".format(email))
        emailcheck = cursor.fetchall()

        cursor.execute("SELECT * FROM `userid` WHERE `username` = '{}'".format(username))
        usernamecheck = cursor.fetchall()
        print("useless: ",usernamecheck)



        if len(emailcheck) > 0:
            flash("Email Already Exists")
        
        elif len(usernamecheck) > 0:
            flash("Username Already Exists")

        elif len(email) < 4:
            flash("email should be greater than 5 characters")
        
        elif len(username) < 6:
            flash("username should be greater than 7 characters")

        elif len(password) < 6:
            flash("password should be greater than 7 characters")

        elif password != confirm_password:
            flash("Incorrect Password")
        
        else:
            cursor.execute("INSERT INTO `userid` (`personID`,`username`, `password`,`email`) VALUES(NULL, '{}','{}','{}')".format(username,password,email))
            mydb.commit()

            cursor.execute("SELECT * FROM userid WHERE username = '{}'".format(username))
            test = cursor.fetchall()
            session["id"] = test[0][0]
            print("test: ", test)

            return redirect("/editProfile")

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop('id')
    return redirect('/')

@app.route("/home")
def home(): 
    if 'id' in session:

        cursor.execute("SELECT username FROM userid where personID = '{}'".format(session["id"]))
        info = cursor.fetchall()
        # print(info)

        cursor.execute("""SELECT follow.following_account , post.post, userid.profile_pic, post.postid
        from follow
        INNER JOIN post on follow.following_account = post.username
        INNER JOIN userid on post.username = userid.username 
        WHERE follow.current_account = '{}'
        ORDER BY post.posttime DESC;
        """.format(info[0][0]))
        allpost = cursor.fetchall()
      

        commentsdict = {}
        likesdict = {}
        counts = {}
        for post in allpost:
            # print(post[3])
            cursor.execute("SELECT comment from comment where postid={}".format(post[3]))
            comments = cursor.fetchall()
            commentsdict[post[3]] = comments
            cursor.execute("SELECT COUNT(postid) from likes WHERE postid = {}".format(post[3]))
            count = cursor.fetchall()
            counts[post[3]] = count
            cursor.execute("SELECT * from likes WHERE user_liked = {} and postid = {}".format(session["id"],post[3]))
            likes = cursor.fetchall()
            likesdict[post[3]] = likes or "1"
    
        # print(likesdict)
        # # print(counts)

        

        # print('commet',commentsdict)
        # # print(allpost)


        return render_template("home.html", value = allpost, commentsdict =commentsdict, likesdict = likesdict, counts = counts)

    else:
        return redirect("/")

@app.route("/profile")
def profile():
    print(session)
    if 'id' in session:
        cursor.execute("SELECT * FROM `userid` WHERE `personID` = '{}'".format(session["id"]))
        user = cursor.fetchall()
        # print("profile user: ",user)

        cursor.execute("SELECT post FROM post WHERE personID = '{}'".format(session["id"]))
        posts = cursor.fetchall()
        print(posts)
        length = len(posts)
        lengthstr = str(length)
        # print(length)

        cursor.execute("SELECT COUNT(current_account) from follow WHERE current_account = '{}'".format(user[0][1]))
        following = cursor.fetchall()
        # print("f" ,following)

        cursor.execute("SELECT COUNT(current_account) from follow WHERE following_account = '{}'".format(user[0][1]))
        followerinfo = cursor.fetchall()
        print("follower:", followerinfo )



        return render_template("profile.html", value = user, value1 = posts, value2 = lengthstr, following = following, followerinfo = followerinfo)



    else:
        return redirect("/")

@app.route("/editProfile", methods = ["POST", "GET"])
def editProfile():
    if "id" in session:

        if request.method == "POST":

            if "file" not in request.files:
                flash("No File Part")
                return redirect(request.url)

            file = request.files["file"]
            
            if file.filename == "":
                flash("No File is Selected")
                return redirect(request.url)

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_name = str(uuid.uuid4()) + "_" + filename
                print(file_name)
                filename = file_name
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                imagepath = path + "\\profile_pic\\" + filename
                print("imagepath:", imagepath)
                replace = imagepath.replace("\\", "/")
                print(replace)

                cursor.execute("UPDATE userid SET profile_pic = '{}' WHERE PersonID = '{}'".format(replace,session["id"]))
                mydb.commit()
                flash ("Profile Pic Updated")
            
            else:
                flash('Allowed file types are txt, pdf, png, jpg, jpeg, gif')
                return redirect(request.url)

            

        return render_template("Edit_Profile.html")
    else:
        return redirect("/")

@app.route("/editProfilename" ,methods = ["POST", "GET"])
def editprofilename():
        if "id" in session:
            if request.method == "POST":
                fullname = request.form.get("fullname")


                if fullname == "":
                    flash("No Name is Type For update")
                
                else:
                
                    cursor.execute("UPDATE userid SET Full_Name = '{}' WHERE personID = '{}'".format(fullname, session["id"]))
                    mydb.commit()
                    flash("Name is Updated")
                    return redirect("/profile")

              

            return redirect("/editProfile")
        else:
            return redirect("/")

@app.route("/upload_Post", methods =["POST", "GET"])
def post():
    if "id" in session:
            if request.method == "POST":
                if "file" not in request.files:
                    flash("No file part")
                    return redirect(request.url)

                file = request.files["file"]

                if file.filename == "":
                    flash("No file is Selected")
                    return redirect(request.url)

                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_name = str(uuid.uuid4()) + "_" + filename
                    filename = file_name
                    file.save(os.path.join(app.config["UPLOAD_FOLDER_POST"], filename))
                    postpath = path + "\\Posts\\" + filename
                    replacepath = postpath.replace("\\","/")
                    print(replacepath)

                    cursor.execute("SELECT username FROM userid WHERE personID = '{}'".format(session["id"]))
                    info = cursor.fetchall()
                    print(info)

                    cursor.execute("INSERT INTO post (`post`, `personID`, `posttime`, `username`) VALUES ('{}','{}',NOW(),'{}')".format(replacepath,session["id"],info[0][0]))
                    mydb.commit()
                    return redirect("/profile") 
            
                else:
                    flash('Allowed file types are txt, pdf, png, jpg, jpeg, gif')
                    return redirect(request.url)
            return render_template("upload_post.html")
    else:
        return redirect("/")

@app.route("/search", methods =["POST","GET"])
def search():
    if "id" in session:
        if request.method == "POST":
            searchuser = request.form.get("searchuser")
            searchuseradd = "%"+searchuser+"%"
            searchuser = searchuseradd
            cursor.execute("SELECT username FROM userid WHERE username like '{}' AND NOT personid = '{}';".format(searchuser,session["id"]))
            usernamesearch1 = cursor.fetchall()
            print(usernamesearch1)
            return render_template("search.html", value = usernamesearch1)

        return render_template("search.html")
    
    else:
        return redirect("/")

@app.route("/search/<username>",)
def searchusername(username):
    if "id" in session:


        cursor.execute("SELECT * FROM userid WHERE username = '{}'".format(username))
        userinfo = cursor.fetchall()
        # print(userinfo)

        cursor.execute("SELECT post FROM post WHERE personID = '{}'".format(userinfo[0][0]))
        posts = cursor.fetchall()
        # print(posts)
        length = len(posts)
        lengthstr = str(length)
        # print(length)

        cursor.execute("SELECT username FROM userid WHERE personID = '{}'".format(session["id"]))
        accountinfo = cursor.fetchall()
        # print(accountinfo)

        cursor.execute("SELECT * FROM follow WHERE current_account = '{}' AND following_account = '{}'".format(accountinfo[0][0], username))
        followinfo = cursor.fetchall()
        numberfollow = len(followinfo)
        # print(len(followinfo))

        cursor.execute("SELECT count(current_account) FROM follow WHERE current_account = '{}'".format(username))
        followinginfo = cursor.fetchall()
        print("following:",followinginfo)

        cursor.execute("SELECT COUNT(current_account) from follow WHERE following_account = '{}'".format(username))
        followerinfo = cursor.fetchall()
        print("follower:", followerinfo )

        


    

        return render_template("searchProfile.html", userinfo = userinfo, post = posts, noofpost = lengthstr, 
        followinfo = numberfollow, followinginfo = followinginfo, followerinfo = followerinfo)

    else:
        return redirect("/")

@app.route("/follow" , methods=["POST"])
def follow():
    if "id" in session:

        data = request.get_data()
        username = data.decode('ASCII')

        cursor.execute("SELECT username FROM userid WHERE personID = '{}'".format(session["id"]))
        userinfo = cursor.fetchall()
        print(userinfo)

        cursor.execute("SELECT * from follow where current_account ='{}' and following_account = '{}' ".format(userinfo[0][0], username))
        check = cursor.fetchall()
        print(len(check))

        if len(check) > 0 :
            # already follow

            cursor.execute("DELETE FROM follow WHERE current_account = '{}' AND following_account = '{}'".format(userinfo[0][0],username))
            mydb.commit()
            print("unfollow")

        else:
            cursor.execute("INSERT INTO follow (current_account,following_account) VALUES ('{}','{}')".format(userinfo[0][0],username))
            mydb.commit()
            print("follow")



        


        


        return jsonify({'message': "done"}) 
        

        


        
    
    else:
        return redirect("/")

@app.route("/comment/<postid>", methods=["POST","GET"])
def comment(postid):
    if "id" in session:

        if request.method == 'POST':
            commentinput = request.form['comment']
            
            print(commentinput)
            print('postid  ',postid)
            # return "done"
        # commentinput = request.form.get("comment")
        # print(commentinput)
        # print(postid)

            cursor.execute("SELECT username FROM userid WHERE personID = '{}'".format(session["id"]))
            sessioninfo = cursor.fetchall()
            print(sessioninfo)
            

            cursor.execute("INSERT INTO comment (postid,user_commented,comment,dateandtime) VALUES ('{}','{}','{}',NOW())".format(postid,sessioninfo[0][0],commentinput))
            mydb.commit()
            return ({'message': 'comment submitted successfully.'})

        # cursor.execute("SELECT * FROM comment WHERE postid = '{}'".format(postid))
        # comments = cursor.fetchall()
        # print(comments)
        # return redirect(request.referrer)
        # make a new page of show comment with link in which it will should full post with all the comments


    else:
        return redirect("/")

@app.route("/post/<postid>")
def posts(postid):
    print(postid)

    cursor.execute("""SELECT post.post, post.username, post.postid, userid.profile_pic
    FROM post
    INNER JOIN userid on post.username = userid.username
    WHERE post.postid = '{}'
     """.format(postid))

    postinfo = cursor.fetchall()
    # print(postinfo)

    cursor.execute("SELECT comment,user_commented FROM comment WHERE postid = '{}'".format(postid))
    comments = cursor.fetchall()
    print(comments)
    
    
    return render_template("post.html", info = postinfo, comments = comments)

@app.route("/likes" , methods = ["POST","GET"])
def like():
    if "id" in session:
        
        data = request.get_data()
        postidd = data.decode('ASCII')
        postid = int(postidd)
        print(postidd)
        
      

        


        cursor.execute("SELECT * FROM likes WHERE postid = '{}' AND user_liked = '{}'".format(postid,session["id"]))
        checking = cursor.fetchall()
        # print((checking))
        
        if len(checking) > 0 :
            cursor.execute("DELETE FROM likes WHERE postid = '{}' AND user_liked = '{}'".format(postid, session["id"]))
            mydb.commit()
        

        else:
            cursor.execute("INSERT INTO likes (postid,user_liked,dateandtime) VALUES ('{}','{}',NOW())".format(postid,session["id"]))
            mydb.commit()

        return jsonify({'message': "done"})

    
    else:
        return redirect("/")

@app.route("/inbox")
def inbox():
    if "id" in session:

        cursor.execute("SELECT username from userid where personID = {}".format(session["id"]))
        userinfo = cursor.fetchall()
        # print(userinfo)

        cursor.execute("SELECT following_account from follow where current_account = '{}'".format(userinfo[0][0]))
        following = cursor.fetchall()


        # print(following)
        # user = message_unread[userinfo[0][0]]
        # print(user)

        return render_template("Messages_inbox.html", value = following )
    else:
        return redirect("/")

@app.route("/inbox/<username>" , methods=["GET","POST"])
def chat(username):
    if "id" in session:

        cursor.execute("SELECT username from userid WHERE personID = '{}'".format(session["id"]))
        userinfo = cursor.fetchall()
        # print(userinfo[0][0])

        cursor.execute("SELECT * from messages WHERE (sender = '{}' and sendto = '{}') or (sender = '{}' and sendto = '{}' ) ".format(userinfo[0][0],username,username,userinfo[0][0]))
        messages = cursor.fetchall()
        # print(messages)

        if username in message_unread[userinfo[0][0]]:
            message_unread[userinfo[0][0]][username] = 0

        return render_template("private_message.html" , username = username, session = userinfo[0][0] , messages = messages)
    
    else:
        return redirect("/")



@Socketio.on('connect')
def connect():
    cursor.execute("SELECT username from userid where personID = '{}'".format(session['id']))
    userinfo = cursor.fetchall()
    # print('connectedd',userinfo[0][0])
    
    if userinfo[0][0] not in message_unread:
        message_unread[userinfo[0][0]] = {}

    currentuser = userinfo[0][0]
    total = sum(message_unread[currentuser].values())

    # print('messagesss',message_unread)
    emit('connect',{"unread":message_unread[currentuser], 'user':userinfo[0][0]})
    emit('unreadmessage',{"unread":message_unread[currentuser]})
    emit('total',{'total': total})
    
    

@Socketio.on('room')
def room(data):
        join_room(data["room"])
        # print("join room", data['room'])
        

@Socketio.on('private_message')
def private_message(data):
    sendto = data['sendto']
    message = data['message']
    sender = data['sender']
    room = data['room']
    # print('sid',request.sid)
    emit('message', {'message':f'<b>{sender}:</b> {message}'}, to = room)


    cursor.execute("INSERT INTO messages(sender,sendto,message,DATE) values('{}','{}','{}',NOW())".format(sender,sendto,message))
    mydb.commit()



@Socketio.on('notification')  
def notification(data):
        
    

    currentuser = data['sendto']
    messagerec_user = data['sender']

    # message_unread[data['sendto']][data['sender']] = 1
    # message_unread[currentuser] = {}
    if messagerec_user in message_unread[currentuser]:
        message_unread[currentuser][messagerec_user] +=1
    else:
        message_unread[currentuser][messagerec_user] = 1
    
    total = sum(message_unread[currentuser].values())

    print('unread  :',message_unread)
    emit('total', {'total': total},to = sessionid[data['sendto']])
    emit('unreadmessage', {"unread": message_unread[currentuser]}, to=sessionid[data['sendto']])
    # print( sessionid[data['sendto']])
    # print(f"notify" ,data['sendto'] )


@Socketio.on('sessionID')
def sessionID(data):

    cursor.execute("SELECT username from userid where personID = '{}'".format(session['id']))
    userinfo = cursor.fetchall()

    sessionid[userinfo[0][0]] = data['id']
    # print(sessionid)
    # print(f'sessionid:', data['id'], 'with session', userinfo[0][0])


@Socketio.on('messageread')
def messageread(data):
    print(data)

# @app.route("/data", methods = ["POST","GET"])
# def sample():
#     if 'id' in session:

#         return render_template("data.html")

#     else:
#         return redirect("/")


# @app.route("/data2", methods = ["POST", "GET"])
# def data2():
#     if request.method == "GET":
#         cursor.execute("SELECT * FROM sample WHERE personid = '{}'".format(2))
#         gettingimage = cursor.fetchall()

    
#     return render_template("data2.html", value = gettingimage)



if __name__ == ("__main__"):
    Socketio.run(app, debug = True)












# SELECT follow.following_account , post.post 
# from follow
# INNER JOIN post on follow.following_account = post.username
# WHERE follow.current_account = "priyansh"


