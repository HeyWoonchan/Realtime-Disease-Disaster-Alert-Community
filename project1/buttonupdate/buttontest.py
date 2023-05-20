from flask import Flask, render_template, request, redirect, jsonify
import requests
import json
from bs4 import BeautifulSoup
import sqlite3

# 데이터베이스 파일 이름
DB_msg = 'database.db'
DB_comment = 'comments.db'
DB_news = 'news.db'

# 메시지 데이터베이스에서 데이터 가져오는 함수
def get_msg_db():
    conn = sqlite3.connect(DB_msg)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM my_table ORDER BY create_date DESC LIMIT 3")
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data

# 댓글 테이블을 생성하는 함수
def create_table():
    conn = sqlite3.connect(DB_comment)
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
url_navernews = 'https://search.naver.com/search.naver?where=news&query=%EB%89%B4%EC%8A%A4%20%EC%86%8D%EB%B3%B4&sort=1&sm=tab_smr&nso=so:dd,p:all,a:all'

app = Flask(__name__)

# 홈 페이지 경로
@app.route('/')
def index():
    return redirect('/home')

# 댓글 페이지 경로
@app.route('/comment')
def comment():
    # 댓글 처리를 위한 로직
    if request.method == 'POST':
        name = request.form['name']
        comment = request.form['comment']
        if name and comment:
            conn = sqlite3.connect(DB_comment)
            c = conn.cursor()
            c.execute("INSERT INTO comments (name, content) VALUES (?, ?)", (name, comment))
            conn.commit()
            conn.close()
            return redirect('/home')
    else:
        conn = sqlite3.connect(DB_comment)
        c = conn.cursor()
        c.execute("SELECT * FROM comments")
        comments = c.fetchall()
        conn.close()
        data = get_msg_db()
        return render_template('comment.html', data=data, comments=comments)

# 홈 페이지 경로 (GET 및 POST 메서드)
@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # 폼 제출 처리를 위한 로직
        name = request.form['name']
        comment = request.form['comment']
        if name and comment:
            conn = sqlite3.connect(DB_comment)
            c = conn.cursor()
            c.execute("INSERT INTO comments (name, content) VALUES (?, ?)", (name, comment))
            conn.commit()
            conn.close()
            return redirect('/home')
    else:
        # 데이터 가져와서 홈 페이지 렌더링
        conn = sqlite3.connect(DB_comment)
        c = conn.cursor()
        c.execute("SELECT * FROM comments")
        comments = c.fetchall()
        conn.close()
        data = get_msg_db()
        return render_template('index.html', data=data, comments=comments)

# 메시지 데이터베이스 업데이트 API 경로
@app.route('/update_msg_db', methods=['POST'])
def update_msg_db():
    response = requests.get(url_api)
    jdata = response.json()
    json_data = json.loads(json.dumps(jdata))
    conn = sqlite3.connect(DB_msg)
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

# 재난 메시지 업데이트를 위한 API 경로
@app.route('/api_disaster_update', methods=['POST'])
def get_disaster_messages():
    response = requests.get(url_api)

    return response.json()

# 뉴스 업데이트를 위한 API 경로
@app.route('/update_news', methods=['POST'])
def update_news():
    response = requests.get(url_news)
    soup = BeautifulSoup(response.content, 'html.parser')
    new_content = str(soup.find_all('a', class_='tit-wrap')[0])
    print(new_content)
    return jsonify({"content": new_content})

# 네이버 뉴스 업데이트를 위한 API 경로
@app.route('/update_news_naver', methods=['POST'])
def update_news_naver():
    response = requests.get(url_navernews)
    soup = BeautifulSoup(response.content, 'html.parser')
    news_articles = str(soup.find_all('a', class_='news_tit')[0].text)
    print(news_articles)
    return jsonify({"content": news_articles})

# 마커 업데이트를 위한 API 경로
@app.route('/update_marker')
def update_marker():
    con = sqlite3.connect(DB_msg, isolation_level=None)
    cursor = con.cursor()
    cursor.execute('select * from my_table order by create_date desc limit 1')
    gotdata = cursor.fetchone()
    address = gotdata[1].split(',')[0]
    what = gotdata[2]

    client_id = 'oa0k1d1gao'  # 발급받은 클라이언트 아이디
    client_secret = 'HVhJUs3dvAA26uPDd7CIL9fhoV3MxP2YwWlnB7FJ'
    url_map = f'https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query={address}'
    headers = {'X-NCP-APIGW-API-KEY-ID': client_id, 'X-NCP-APIGW-API-KEY': client_secret}

    response = requests.get(url_map, headers=headers)
    data = response.json()

    print(address)

    if 'addresses' in data:
        if len(data['addresses']) > 0:
            latitude = data['addresses'][0]['y']  # 위도
            longitude = data['addresses'][0]['x']  # 경도
            print(latitude, longitude, what)
            return jsonify({'latitude': latitude, 'longitude': longitude, 'what': what})
        else:
            print("주소를 찾을 수 없습니다.")
    else:
        print("API 요청에 실패했습니다.")

# 애플리케이션 실행
if __name__ == "__main__":
    create_table()
    app.run(host='localhost', port=8023)
