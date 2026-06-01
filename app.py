import tflearn
import numpy as np
import pandas as pd
import pickle,random
import json
import sqlite3
import nltk
import MySQLdb
from nltk.stem.lancaster import LancasterStemmer
from playsound import playsound
import speech_recognition as sr
from tensorflow import keras
from tensorflow.keras.models import load_model
from models import Model1
import tensorflow as tf
from gtts import gTTS
import os
from werkzeug.utils import secure_filename
from PIL import Image

import os
import pyttsx3
stemmer = LancasterStemmer()

from flask import Flask,render_template,request,redirect,url_for,session
import real_time_video as emotion
app = Flask(__name__)
app.static_folder = 'static'
app.config['SECRET_KEY'] = 'secret!'
import MySQLdb
UPLOAD_FOLDER = 'static/profile_photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

mydb = MySQLdb.connect(host='localhost',user='root',passwd='root',db='mentalchatbot')

file1 = open("data.txt","a")
with open("assets/input_data.pickle", "rb") as f:
        words, labels, training, output = pickle.load(f)

with open("assets/sample.json") as myfile:
        data = json.load(myfile)

#tf.reset_default_graph()

network = tflearn.input_data(shape=[None, len(training[0])])

network = tflearn.fully_connected(network,8)
network = tflearn.fully_connected(network,8)

network = tflearn.fully_connected(network,len(output[0]),activation="softmax")
network = tflearn.regression(network)

model = tflearn.DNN(network)

model.load("assets/chatbot.tflearn")

def predict_class(sentence, model):
    # filter out predictions below a threshold
    p = bow(sentence, words,show_details=False)
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i,r] for i,r in enumerate(res) if r>ERROR_THRESHOLD]
    # sort by strength of probability
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list

def getResponse(ints, intents_json):
    tag = ints[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if(i['tag']== tag):
            result = random.choice(i['responses'])
            break
    return result
def bag_of_words(s,words):
	bag = [0 for _ in range(len(words))]

	s_words = nltk.word_tokenize(s)
	s_words = [stemmer.stem(word.lower()) for word in s_words]

	for se in s_words:
		for i,w in enumerate(words):
			if w == se:
				bag[i] = 1

	return np.array(bag)

def chatbot_response(inp):
    results = model.predict([bag_of_words(inp,words)])[0]
    #print(results)
    results_index = np.argmax(results)
    tag = labels[results_index]
    #print(tag)  
    if results[results_index] < 0.8 or len(inp)<2:
       results="Sorry, I didn't get you. Please try again."
    else:
        for tg in data['intents']:
            if tg['tag'] == tag:
                responses = tg['responses']
                results=random.choice(responses)
    engine = pyttsx3.init()
    engine.say(str(results))
    engine.runAndWait()
    file1.write("Bot : ")
    file1.write(str(results))

    file1.write("\n")
    return results



    
@app.route("/")
def home():
    return render_template("home.html")
@app.route('/logon')
def logon():
        return render_template('signup.html')
@app.route('/quizpage')
def quizpage():
        username=session['cid']

        return render_template('quizpage.html',user=username)

@app.route('/login')
def login():
	session.clear()
	return render_template('signin.html')
@app.route('/predict', methods=["POST"])
def predict():
        username = session['cid']
        global temo
        quizres = ""
        quizscore = 0
        print("User Name==", username)
        
        q1 = int(request.form['a1'])
        q2 = int(request.form['a2'])
        q3 = int(request.form['a3'])
        q4 = int(request.form['a4'])
        q5 = int(request.form['a5'])
        q6 = int(request.form['a6'])
        q7 = int(request.form['a7'])
        q8 = int(request.form['a8'])
        q9 = int(request.form['a9'])
        q10 = int(request.form['a10'])
        
        values = [q1, q2, q3, q4, q5, q6, q7, q8, q9, q10]
        model1 = Model1()
        classifier = model1.svm_classifier()
        prediction = classifier.predict([values])
        
        if prediction[0] == 0:
                result = 'Your Depression test result : No Depression'
                quizres = "No Depression"
                quizscore = 100
        if prediction[0] == 1:
                result = 'Your Depression test result : Mild Depression'
                quizres = "Mild Depression"
                quizscore = 70
        if prediction[0] == 2:
                result = 'Your Depression test result : Moderate Depression'
                quizres = "Moderate Depression"
                quizscore = 50
        if prediction[0] == 3:
                result = 'Your Depression test result : Moderately severe Depression'
                quizres = "Moderately severe Depression"
                quizscore = 20
        if prediction[0] == 4:
                result = 'Your Depression test result : Severe Depression'
                quizres = "Severe Depression"
                quizscore = 10
        
        temo = quizscore
        
        # Get previous quiz score
        cur1 = mydb.cursor()
        cur1.execute("select qizscore from quizscore where uname='" + str(username) + "' ORDER BY dat DESC")
        data = cur1.fetchone()
        
        # Insert current quiz score
        cur = mydb.cursor()
        cur.execute("insert into quizscore (uname,qizscore,qizres,dat) VALUES (%s, %s, %s, now())", (username, quizscore, quizres))
        mydb.commit()
        
        # FIX: Handle case when no previous data exists (first time user)
        if data is not None and len(data) > 0:
            previousscore = data[0]
        else:
            previousscore = 50
        
        prevresult = ""
        print("previousscore==", previousscore)
        
        if float(quizscore) < float(previousscore):
            prevresult = "You're doing well, and it seems like you're facing some challenges. Remember, it's okay to seek help and practice self-care."
        else:
            prevresult = "Great news! Your mental health is improving. Keep up the positive actions! "
        
        print("prevresult==", prevresult)
        
        # Calculate average score from emotion and quiz
        totalscore = float(femo) + float(temo)
        avgscore = float(totalscore) / 2
        result = ""
        print("avgscore==",avgscore)
        
        # Determine result based on average score
        if float(avgscore) >= 95:
            result = "Yay! You are normal. Keep going"
            return render_template("index.html", result=result)
        if float(avgscore) >= 75 and float(avgscore) < 95:
            result = "You're doing great, but there might be some stress. Consider taking some time to relax and unwind"
            return render_template("stress.html", result=result)
        if float(avgscore) >= 50 and float(avgscore) < 75:
            result = "You're managing well, though you may be experiencing some anxiety. Remember to take deep breaths and give yourself some self-care."
            return render_template("Anixity.html", result=result)
        # FIX: Corrected the condition syntax
        if float(avgscore) >= 0 and float(avgscore) < 50:
            result = "You're strong, and it looks like you might be feeling down. It's important to talk to someone you trust and take small steps towards feeling better."
            return render_template("depression.html", result=result)

@app.route("/sos")
def sos():
    return render_template("sos.html")
@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('user', '')
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        number = request.form.get('mobile', '')
        password = request.form.get('password', '')
        
        # Handle profile photo upload
        profile_photo = 'default_avatar.png'
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"{username}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Resize image to 200x200
                img = Image.open(filepath)
                img = img.resize((200, 200))
                img.save(filepath)
                
                profile_photo = f"profile_photos/{filename}"
        
        mydb = MySQLdb.connect(host='localhost', user='root', passwd='root', db='mentalchatbot')
        cur = mydb.cursor()
        cur.execute("INSERT INTO reg (user, email, password, mobile, name, profile_photo) VALUES (%s, %s, %s, %s, %s, %s)",
                   (username, email, password, number, name, profile_photo))
        mydb.commit()
        mydb.close()
        return render_template("signin.html")
    
    return render_template("signup.html")


@app.route("/getemotion")
def getemotion():
        username=session['cid']
        global femo
        print("User Name==",username)
        emot=emotion.process()
        print("Emotion==",emot)
        emoscore=0
        if emot=="angry":
                emoscore=0
        if emot=="disgust":
                emoscore=10
        if emot=="scared":
                emoscore=10
        if emot=="happy":
                emoscore=100
        if emot=="sad":
                emoscore=10
        if emot=="surprised":
                emoscore=80
        if emot=="neutral":
                emoscore=60
        femo=emoscore
        
        cur1 = mydb.cursor()
        cur1.execute("select emscore from fes where uname='"+str(username)+"' ORDER BY dat DESC")
        data = cur1.fetchone()
        
        cur = mydb.cursor()
        cur.execute("insert into fes (uname,emotion,emscore,dat) VALUES (%s, %s, %s, now())",(username,emot,emoscore))
        mydb.commit()
        
        # FIX: Check if data is None before trying to get its length
        if data is not None and len(data) > 0:
            previousscore = data[0]
        else:
            previousscore = 50
            
        prevresult = ""
        print("previousscore==", previousscore)

        if float(emoscore) < float(previousscore):
            prevresult = "You're doing well, and it seems like you're facing some challenges. Remember, it's okay to seek help and practice self-care."
        else:
            prevresult = "Great news! Your mental health is improving. Keep up the positive actions! "
            
        print("prevresult==", prevresult)

        return render_template("quizpage.html", prevresult=prevresult)
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    mydb = MySQLdb.connect(host='localhost', user='root', passwd='root', db='mentalchatbot')

    if request.method == 'POST':
        mail1 = request.form.get('user', '')
        password1 = request.form.get('password', '')

        cur = mydb.cursor()
        cur.execute("SELECT user, password, profile_photo, name, email, mobile FROM reg WHERE user = %s AND password = %s", (mail1, password1))
        data = cur.fetchone()

        if data:
            session['cid'] = data[0]
            session['profile_photo'] = data[2] if data[2] else 'default_avatar.png'

            profile_photo = session['profile_photo']

            return redirect(url_for('index'))
            
        else:
            return render_template("signin.html", error="Invalid credentials")

    return render_template("signin.html")


@app.route("/index")
def index():
    if 'cid' not in session:
        return redirect(url_for('login'))

    username = session['cid']
    profile_photo = session.get('profile_photo', 'default_avatar.png')

    mydb = MySQLdb.connect(host='localhost', user='root', passwd='root', db='mentalchatbot')
    cur = mydb.cursor()

    # Chat history
    cur.execute("SELECT message, response FROM chat_history WHERE username=%s ORDER BY id ASC", (username,))
    chats = cur.fetchall()

    # Emotion scores (FES)
    cur.execute("SELECT emscore, DATE(dat) FROM fes WHERE uname=%s ORDER BY dat ASC", (username,))
    fes_data = cur.fetchall()

    # Quiz scores
    cur.execute("SELECT qizscore, DATE(dat) FROM quizscore WHERE uname=%s ORDER BY dat ASC", (username,))
    quiz_data = cur.fetchall()

    mydb.close()

    # Prepare lists
    dates = []
    emo_scores = []
    quiz_scores = []
    avg_scores = []

    for i in range(len(fes_data)):
        dates.append(str(fes_data[i][1]))
        emo = float(fes_data[i][0])
        quiz = float(quiz_data[i][0]) if i < len(quiz_data) else 0

        emo_scores.append(emo)
        quiz_scores.append(quiz)
        avg_scores.append((emo + quiz) / 2)

    return render_template(
        "index.html",
        profile_photo=profile_photo,
        chats=chats,
        dates=dates,
        emo_scores=emo_scores,
        quiz_scores=quiz_scores,
        avg_scores=avg_scores
    )


@app.route("/logout")
def logout():
    session.clear()
    return render_template('signin.html')
@app.route("/profile_settings")
def profile_settings():
    if 'cid' not in session:
        return redirect(url_for('login'))
    
    username = session['cid']
    mydb = MySQLdb.connect(host='localhost', user='root', passwd='root', db='mentalchatbot')
    cur = mydb.cursor()
    cur.execute("SELECT name, email, mobile, profile_photo FROM reg WHERE user = %s", (username,))
    data = cur.fetchone()
    mydb.close()
    
    profile_photo_url = url_for('static', filename=data[3]) if data[3] else url_for('static', filename='default_avatar.png')
    
    return render_template("profile_settings.html", 
                         username=username,
                         name=data[0],
                         email=data[1],
                         mobile=data[2],
                         profile_photo_url=profile_photo_url)
@app.route("/update_profile", methods=['POST'])
def update_profile():
    if 'cid' not in session:
        return redirect(url_for('login'))
    
    username = session['cid']
    name = request.form.get('name', '')
    email = request.form.get('email', '')
    mobile = request.form.get('mobile', '')
    
    mydb = MySQLdb.connect(host='localhost', user='root', passwd='root', db='mentalchatbot')
    
    # Handle profile photo update
    profile_photo = None
    if 'profile_photo' in request.files:
        file = request.files['profile_photo']
        if file and file.filename != '' and allowed_file(file.filename):
            # Delete old photo if not default
            cur = mydb.cursor()
            cur.execute("SELECT profile_photo FROM reg WHERE user = %s", (username,))
            old_photo = cur.fetchone()[0]
            if old_photo and old_photo != 'default_avatar.png':
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(old_photo))
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            filename = secure_filename(f"{username}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Resize image
            img = Image.open(filepath)
            img = img.resize((200, 200))
            img.save(filepath)
            
            profile_photo = f"profile_photos/{filename}"
    
    # Update user information
    cur = mydb.cursor()
    if profile_photo:
        cur.execute("UPDATE reg SET name=%s, email=%s, mobile=%s, profile_photo=%s WHERE user=%s",
                   (name, email, mobile, profile_photo, username))
        session['profile_photo'] = profile_photo
    else:
        cur.execute("UPDATE reg SET name=%s, email=%s, mobile=%s WHERE user=%s",
                   (name, email, mobile, username))
    
    mydb.commit()
    mydb.close()
    
    # Update session
    session['user_name'] = name
    session['user_email'] = email
    session['user_mobile'] = mobile
    
    return render_template("profile_settings.html", 
                         username=username,
                         name=name,
                         email=email,
                         mobile=mobile,
                         profile_photo_url=url_for('static', filename=session.get('profile_photo', 'default_avatar.png')),
                         message="Profile updated successfully!",
                         message_type="success")

@app.route("/record")
def record():
    text=""
    while(text==""):
        #voice recognition part
        r = sr.Recognizer()
        m = sr.Microphone()
        #set threhold level
        with m as source: r.adjust_for_ambient_noise(source)#recognize
        with sr.Microphone() as source:
            print ("Your choice:")
            audio=r.listen(source)
            print ("ok done!!")
        try:
            text=r.recognize_google(audio)
            print ("You said : "+text)
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio.")
        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e)) 
        if text=="":
            tts = gTTS(text="Error in Message.Please Give Input Again ", lang='en')
            ran=random.randint(0,999)
            ttsname=("err"+str(ran)+".mp3") 
            tts.save(ttsname)
            playsound(ttsname)
            os.remove(ttsname)
        else:
            return render_template("index.html",data=text)


@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    username = session.get('cid')

    bot_response = chatbot_response(userText)

    # Save to DB
    mydb = MySQLdb.connect(host='localhost', user='root', passwd='root', db='mentalchatbot')
    cur = mydb.cursor()
    cur.execute(
        "INSERT INTO chat_history (username, message, response) VALUES (%s, %s, %s)",
        (username, userText, bot_response)
    )
    mydb.commit()
    mydb.close()

    return bot_response




  
if __name__ == "__main__":
    app.run(debug=True)
    