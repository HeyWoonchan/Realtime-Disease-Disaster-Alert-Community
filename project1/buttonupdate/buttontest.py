from flask import Flask, render_template, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import json
from bs4 import BeautifulSoup
import sqlite3

def get_msg_db():
    conn = sqlite3.connect('project1/buttonupdate/static/database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM my_table ORDER BY create_date DESC LIMIT 3")
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


url_news = "https://www.yna.co.kr/theme/breaknews-history"
url_api = "http://apis.data.go.kr/1741000/DisasterMsg3/getDisasterMsg1List?serviceKey=DCEWLmC5o0ec6lJ%2FsTpRPUFLDnn8eH24STfRT5ZxbqR9BQBOk0i484ELM%2BBMVgC3YDKc8SiGrtkcs17Skrp97A%3D%3D&pageNo=1&numOfRows=3&type=json"

app = Flask(__name__)
@app.route('/')
def index():
    return render_template('main.html')


@app.route('/home')
def home():

    
    data = get_msg_db()

    return render_template('index.html', data = data)


@app.route('/update_msg_db', methods=['POST'])
def update_msg_db():
    response = requests.get(url_api)
    jdata = response.json()
    json_data = json.loads(json.dumps(jdata))
    conn = sqlite3.connect('project1/buttonupdate/static/database.db')
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


if __name__ == "__main__":
    app.run(port=8000)