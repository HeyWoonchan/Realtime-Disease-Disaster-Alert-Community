from flask import Flask, render_template, request, redirect, jsonify
import requests
import json
from bs4 import BeautifulSoup
import sqlite3
import googlemaps

# 데이터베이스 파일 이름
DB_comment = 'comments.db'
DB_news = 'news.db'
DB_internal_msg = 'database.db'
DB_external_msg = 'ForSafeTrip.db'


#재난문자 type으로 차트를 생성
def get_chart_data():
    # SQLite 데이터베이스 연결
    conn = sqlite3.connect(DB_internal_msg)
    cursor = conn.cursor()

    # 최근 5일의 데이터 조회
    cursor.execute("SELECT DISTINCT create_date FROM my_table ORDER BY create_date DESC LIMIT 50")
    dates = cursor.fetchall()
    dates = [date[0].split()[0] for date in dates]

    # 각 날짜별 type의 개수 조회
    chart_data = {}
    for date in dates:
        chart_data[date] = {'undefined': 0, 'missing': 0, 'disaster': 0}

    for date in chart_data.keys():
        cursor.execute(f"SELECT type, COUNT(*) FROM my_table WHERE create_date LIKE '{date}%' GROUP BY type")
        rows = cursor.fetchall()
        for row in rows:
            chart_data[date][row[0]] = row[1]

    # 데이터베이스 연결 종료
    cursor.close()
    conn.close()

    return chart_data

# 재난문자 데이터베이스에서 데이터 가져오는 함수
def get_msg_db():
    conn = sqlite3.connect(DB_internal_msg)
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

    conn = sqlite3.connect(DB_internal_msg)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS my_table (
                    create_date TEXT,
                    location_name TEXT,
                    msg TEXT,
                    type TEXT
                )''')
    conn.commit()
    conn.close()




url_news = "https://www.yna.co.kr/theme/breaknews-history"
url_api = "http://apis.data.go.kr/1741000/DisasterMsg3/getDisasterMsg1List?serviceKey=DCEWLmC5o0ec6lJ%2FsTpRPUFLDnn8eH24STfRT5ZxbqR9BQBOk0i484ELM%2BBMVgC3YDKc8SiGrtkcs17Skrp97A%3D%3D&pageNo=1&numOfRows=10&type=json"
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
        # 댓글 폼 제출 처리를 위한 로직
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

        chart_data = get_chart_data()
        conn = sqlite3.connect(DB_comment)
        c = conn.cursor()
        c.execute("SELECT * FROM comments")
        comments = c.fetchall()
        conn.close()
        data = get_msg_db()
        dates = list(chart_data.keys())[::-1] 
        return render_template('index.html', data=data, comments=comments, chart_data=chart_data,dates=dates)
    
#해외 페이지 
@app.route('/external')
def external():
    return render_template('external.html')

# 메시지 데이터베이스 업데이트 API 경로
@app.route('/update_msg_db', methods=['POST'])
def update_msg_db():
    response = requests.get(url_api)
    jdata = response.json()
    json_data = json.loads(json.dumps(jdata))
    conn = sqlite3.connect(DB_internal_msg)
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS my_table (
                        create_date TEXT,
                        location_name TEXT,
                        msg TEXT,
                        type TEXT
                    )''')

    # 단어 목록과 해당 타입 지정
    disaster_words = ['지진', '산불', '화재']
    missing_words = ['실종', '찾습니다']

    for item in json_data['DisasterMsg'][1]['row']:
        create_date = item['create_date']
        location_name = item['location_name']
        msg = item['msg']

        # msg에 있는 단어를 확인하여 type 설정
        if any(word in msg for word in disaster_words):
            msg_type = 'disaster'
        elif any(word in msg for word in missing_words):
            msg_type = 'missing'
        else:
            msg_type = 'undefined'

        cursor.execute("SELECT * FROM my_table WHERE create_date = ? AND location_name = ? AND msg = ?",
                    (create_date, location_name, msg))
        existing_data = cursor.fetchone()

        if existing_data:
            print("Data already exists in the database.")
        else:
            cursor.execute("INSERT INTO my_table (create_date, location_name, msg, type) VALUES (?, ?, ?, ?)",
                        (create_date, location_name, msg, msg_type))
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

# 국내 마커 업데이트를 위한 API 경로
@app.route('/update_marker_internal')
def update_marker1():
    con = sqlite3.connect(DB_internal_msg, isolation_level=None)
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


# 해외 마커 업데이트를 위한 API 경로
@app.route('/update_marker_external')
def update_marker2():
    con = sqlite3.connect(DB_external_msg, isolation_level=None)
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


# 애플리케이션 실행
if __name__ == "__main__":
    create_table()
    app.run(host='localhost', port=8023)
