from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
import requests
import json
from bs4 import BeautifulSoup
import sqlite3
import pytz
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired 




# 데이터베이스 파일 이름
DB_msg = 'database.db'
DB_comment = 'comments.db'
DB_news = 'news.db'


#재난문자 type으로 차트를 생성
def get_chart_data():
    # SQLite 데이터베이스 연결
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # 최근 데이터 조회
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

    conn = sqlite3.connect(DB_msg)
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
#커뮤니티 페이지용
app.config['SECRET_KEY'] = 'mysecretkey1232'
db_path = os.path.join(os.path.dirname(__file__), 'test.db')
db_uri = 'sqlite:///{}'.format(db_path)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
db = SQLAlchemy(app)


seoul_tz = pytz.timezone('Asia/Seoul')




# 홈 페이지 경로


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
@app.route('/', methods=['GET', 'POST'])
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
            return redirect('/')
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

#커뮤니티 페이지 전용 ----------------

# 게시글
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(50))

    def __repr__(self):
        return '<Post %r>' % self.title
    
class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')
    author = StringField('Author', validators=[DataRequired()])
    topic = SelectField('Topic', choices=[('Disaster/Disease', 'Disaster/Disease'), ('Real-time', 'Real-time'), ('Others', 'Others')])

#댓글
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    author = db.Column(db.String(100), nullable=False)

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Submit')
    author = StringField('Author', validators=[DataRequired()])


@app.route('/community')
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page=page, per_page=10)
    return render_template('community.html', posts=posts)

@app.route('/community/create', methods=['GET', 'POST'])
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        new_post = post = Post(title=form.title.data, content=form.content.data, author=form.author.data, topic=form.topic.data, timestamp=datetime.now(seoul_tz))

        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('create_post.html', form=form)

@app.route('/community/post/<int:post_id>', methods=['GET', 'POST'])
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post_id).all()
    form = CommentForm()

    if form.validate_on_submit():
        comment = comment = Comment(content=form.content.data, author=form.author.data, post_id=post.id, timestamp=datetime.now(seoul_tz))

        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been added.', 'success')
        return redirect(url_for('post_detail', post_id=post.id))

    return render_template('post_detail.html', post=post, comments=comments, form=form)


@app.route('/community/post/<int:post_id>/comment', methods=['GET', 'POST'])
def comment_post(post_id):
    form = CommentForm()
    post = Post.query.get_or_404(post_id)
    if form.validate_on_submit():
        comment = Comment(content=form.content.data, author=form.author.data, post_id=post.id, timestamp=datetime.now(seoul_tz))
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been added.', 'success')
        return redirect(url_for('post_detail', post_id=post_id))
    return render_template('comment_post.html', title='New Comment', form=form)




# 애플리케이션 실행
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    create_table()
    
    app.run(host='localhost', port=8023)
