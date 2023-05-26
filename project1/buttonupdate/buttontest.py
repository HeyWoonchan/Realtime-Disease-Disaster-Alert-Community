from flask import Flask, render_template,request, redirect,jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import json
import os.path
from bs4 import BeautifulSoup
import sqlite3
import googlemaps


DATABASE = 'comments.db'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
msgdb_path = os.path.join(BASE_DIR, 'database.db')
exdb_path = os.path.join(BASE_DIR, 'ForSafeTrip.db')

def get_msg_db():
    conn = sqlite3.connect(msgdb_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM my_table ORDER BY create_date DESC LIMIT 3")
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


def create_table():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    content TEXT NOT NULL
                )''')
    conn.commit()
    conn.close()


url_news = "https://www.yna.co.kr/theme/breaknews-history"
url_api = "http://apis.data.go.kr/1741000/DisasterMsg3/getDisasterMsg1List?serviceKey=DCEWLmC5o0ec6lJ%2FsTpRPUFLDnn8eH24STfRT5ZxbqR9BQBOk0i484ELM%2BBMVgC3YDKc8SiGrtkcs17Skrp97A%3D%3D&pageNo=1&numOfRows=3&type=json"

app = Flask(__name__)
@app.route('/')
def index():
    return render_template('main.html')

@app.route('/external')
def ex():
    return render_template('external.html')

@app.route('/comment')

@app.route('/home', methods=['GET', 'POST'])
def home():
    
    if request.method == 'POST':
        name = request.form['name']
        comment = request.form['comment']
        if name and comment:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("INSERT INTO comments (name, content) VALUES (?, ?)", (name, comment))
            conn.commit()
            conn.close()
            return redirect('/home')
    else:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM comments")
        comments = c.fetchall()
        conn.close()
        data = get_msg_db()
        return render_template('index.html',data=data, comments=comments)
    


@app.route('/update_msg_db', methods=['POST'])
def update_msg_db():
    response = requests.get(url_api)
    jdata = response.json()
    json_data = json.loads(json.dumps(jdata))
    conn = sqlite3.connect(msgdb_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS my_table (
                        create_date TEXT,
                        location_name TEXT,
                        msg TEXT
                    )''')
    for item in json_data['DisasterMsg'][1]['row']:
        create_date = item['create_date']
        location_name = item['location_name']
        msg = item['msg']
        cursor.execute("SELECT * FROM my_table WHERE create_date = ? AND location_name = ? AND msg = ?",
                   (create_date, location_name, msg))
        existing_data = cursor.fetchone()

        if existing_data:
            print("Data already exists in the database.")
        else:
            cursor.execute("INSERT INTO my_table (create_date, location_name, msg) VALUES (?, ?, ?)",
                        (create_date, location_name, msg))
            conn.commit()
            print("Data added to the database.")
        
    conn.commit()
    conn.close()
    return jsonify({'data': '업데이트 완료'})


@app.route('/api_disaster_update', methods=['POST'])
def get_disaster_messages():
    response = requests.get(url_api)

    return response.json()

@app.route('/update_news', methods=['POST'])
def update_news():
    response = requests.get(url_news)
    soup = BeautifulSoup(response.content, 'html.parser')
    new_content = str(soup.find_all('a', class_='tit-wrap')[0])
    print(new_content)
    return jsonify({"content": new_content})

@app.route('/update_marker_internal')
def update_marker1():
    con = sqlite3.connect(msgdb_path, isolation_level=None)
    cursor = con.cursor()
    cursor.execute('select * from my_table order by create_date desc limit 1')
    gotdata = cursor.fetchone()
    where = gotdata[1]
    what = gotdata[2]

    api_key = 'AIzaSyCnp17nNrPOjhrQk4Pp7HUVfMGzyqGw5eI'
    maps = googlemaps.Client(key=api_key)

    results = maps.geocode(where)

    for result in results:
        address = result['geometry']['location']
        print(address['lat'], address['lng'], what)
        return jsonify({'latitude' : address['lat'], 'longitude': address['lng'], 'what' : what})
    
@app.route('/update_marker_external')
def update_marker2():
    con = sqlite3.connect(exdb_path, isolation_level=None)
    cursor = con.cursor()
    cursor.execute('select * from ForSafeTrip order by id asc limit 1')
    gotdata = cursor.fetchone()
    where = gotdata[1]
    what = gotdata[2]

    api_key = 'AIzaSyCnp17nNrPOjhrQk4Pp7HUVfMGzyqGw5eI'
    maps = googlemaps.Client(key=api_key)

    results = maps.geocode(where)

    for result in results:
        address = result['geometry']['location']
        print(address['lat'], address['lng'], what)
        return jsonify({'latitude' : address['lat'], 'longitude': address['lng'], 'what' : what})


if __name__ == "__main__":
    create_table()
    app.run(host='localhost', port=8042)