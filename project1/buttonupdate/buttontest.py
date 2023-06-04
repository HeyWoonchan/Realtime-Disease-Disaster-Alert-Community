from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
import requests, json, sqlite3, pytz, os, googlemaps, time
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired 

# 데이터베이스 파일 이름
DB_comment = 'comments.db'
DB_news = 'news.db'
DB_internal_msg = 'database.db'
DB_external_msg = 'ForSafeTrip.db'
DB_WHOnews = 'ExternalNews.db'

last_execution_time = 0
last_execution_time_safetrip = 0

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

def get_msg_db_emerg():
    conn = sqlite3.connect(DB_internal_msg)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM my_table WHERE type IN ('disaster', 'emergency') ORDER BY create_date DESC LIMIT 3")
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data

# 재난문자 데이터베이스 업데이트 함수
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
    emergency_words = ['대피', '행정안전부']

    for item in json_data['DisasterMsg'][1]['row']:
        create_date = item['create_date']
        location_name = item['location_name']
        msg = item['msg']

        # msg에 있는 단어를 확인하여 type 설정
        if any(word in msg for word in disaster_words):
            msg_type = 'disaster'
        elif any(word in msg for word in missing_words):
            msg_type = 'missing'
        elif any(word in msg for word in emergency_words):
            msg_type = 'emergency'
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
url_api = "http://apis.data.go.kr/1741000/DisasterMsg3/getDisasterMsg1List?serviceKey=DCEWLmC5o0ec6lJ%2FsTpRPUFLDnn8eH24STfRT5ZxbqR9BQBOk0i484ELM%2BBMVgC3YDKc8SiGrtkcs17Skrp97A%3D%3D&pageNo=1&numOfRows=20&type=json"
url_navernews = 'https://search.naver.com/search.naver?where=news&query=%EB%89%B4%EC%8A%A4%20%EC%86%8D%EB%B3%B4&sort=1&sm=tab_smr&nso=so:dd,p:all,a:all'
url_safetrip = "https://www.0404.go.kr/dev/newest_list.mofa"
url_safetrip_view = "https://www.0404.go.kr/dev/newest_view.mofa"
app = Flask(__name__)


def update_safetrip():
    conn = sqlite3.connect('ForSafeTrip.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM ForSafeTrip')


    # SafeTrip 테이블 생성
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS ForSafeTrip (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country TEXT,
        title TEXT,
        link TEXT
    )
    '''
    cursor.execute(create_table_query)

    # 페이지 순회 및 데이터 크롤링
    for page in range(1, 2):  # 1부터 5까지의 페이지 크롤링
        params = {
            "id": "",
            "pagenum": str(page),
            "mst_id": "MST0000000000041",
            "ctnm": "",
            "div_cd": "",
            "st": "title",
            "stext": ""
        }

        response = requests.get(url_safetrip, params=params)
        soup = BeautifulSoup(response.content, 'html.parser')
        global_news = soup.find_all('td', class_='subject')
        global_countries = soup.find_all('td', class_='bb_ctr1')

        for news, country in zip(global_news, global_countries):
            title = news.text.strip()
            link = news.a

            if link is not None:
                # 자바스크립트 형식의 링크를 URL 형식으로 변환
                link_text = urljoin(url_safetrip, link['href']).replace("javascript:goview(", "").replace(")", "").replace("'","")
                link_text = f"{url_safetrip_view}?id={link_text}&pagenum=1&mst_id=MST0000000000041&ctnm=&div_cd=&st=title&stext="
            else:
                link_text = ""

            country_name = country.text.strip()

            # 데이터 삽입
            if country_name != '전체국가':
                insert_query = 'INSERT INTO ForSafeTrip (country, title, link) VALUES (?, ?, ?)'
                cursor.execute(insert_query, (country_name, title, link_text))

            print(f"국가: {country_name}")
            print(f"제목: {title}")
            print(f"링크: {link_text}")
            print()

        print(f"--- {page} 페이지 크롤링 완료 ---")
        print()

    # 변경사항 저장
    conn.commit()
    conn.close()

#커뮤니티 페이지용
app.config['SECRET_KEY'] = 'mysecretkey1232'
db_path = os.path.join(os.path.dirname(__file__), 'test.db')
db_uri = 'sqlite:///{}'.format(db_path)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
db = SQLAlchemy(app)
seoul_tz = pytz.timezone('Asia/Seoul')


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
            return redirect('/')
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
    global last_execution_time
    current_time = time.time()
    print(os.getcwd())
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
       
        if current_time - last_execution_time >= 15:
            last_execution_time = current_time
            update_msg_db()
        print(current_time, last_execution_time)
        chart_data = get_chart_data()
        conn = sqlite3.connect(DB_comment)
        c = conn.cursor()
        c.execute("SELECT * FROM comments")
        comments = c.fetchall()
        conn.close()
        data = get_msg_db()
        yh_news=update_news()
        data_emerg = get_msg_db_emerg()
        nv_news=update_news_naver()
        dates = list(chart_data.keys())[::-1] 
        return render_template('index.html', yh_news=yh_news, nv_news=nv_news ,data=data, data_emerg=data_emerg, comments=comments, chart_data=chart_data,dates=dates)
    
#해외 페이지 
@app.route('/external')
def external():
    global last_execution_time_safetrip
    nowtime = time.time()
    if nowtime-last_execution_time_safetrip>60:
        last_execution_time_safetrip=nowtime
        update_safetrip()
    return render_template('external.html')


# 재난 메시지 업데이트를 위한 함수
@app.route('/api_disaster_update', methods=['POST'])
def get_disaster_messages():
    response = requests.get(url_api)

    return response.json()

# 뉴스 업데이트를 위한 함수
def update_news():
    response = requests.get(url_news)
    soup = BeautifulSoup(response.content, 'html.parser')
    new_content = soup.find_all('a', class_='tit-wrap')[0]
    print(new_content)
    return new_content

# 네이버 뉴스 업데이트를 위한 API 경로
def update_news_naver():
    response = requests.get(url_navernews)
    soup = BeautifulSoup(response.content, 'html.parser')
    news_articles = str(soup.find_all('a', class_='news_tit')[0].text)
    print(news_articles)
    return news_articles

# 국내 마커 업데이트를 위한 API 경로

@app.route('/update_marker_internal')
def update_marker_in():
    con = sqlite3.connect(DB_internal_msg, isolation_level=None)
    cursor = con.cursor()
    cursor.execute('select * from my_table order by create_date desc limit 3')
    gotdata = cursor.fetchall()

    api_key = 'AIzaSyCnp17nNrPOjhrQk4Pp7HUVfMGzyqGw5eI'
    maps = googlemaps.Client(key=api_key)

    marker_data = []

    for row in gotdata:
        where = row[1]
        what = row[2]
        
        results = maps.geocode(where)

        for result in results:
            address = result['geometry']['location']
            print(address['lat'], address['lng'], what)
            marker_data.append({'latitude' : address['lat'], 'longitude': address['lng'], 'what' : what})
    
    return jsonify(marker_data)


# 해외 안전 정보 업데이트를 위한 API 경로
@app.route('/update_external')
def update_marker_ex():
    con = sqlite3.connect(DB_external_msg, isolation_level=None)
    cursor = con.cursor()
    cursor.execute('select * from ForSafeTrip order by id asc limit 3')
    gotdata = cursor.fetchall()
    api_key = 'AIzaSyCnp17nNrPOjhrQk4Pp7HUVfMGzyqGw5eI'
    maps = googlemaps.Client(key=api_key)

    marker_data = []
    for row in gotdata:
        where = row[1]
        what = row[2]
        link = row[3]
        results = maps.geocode(where)

        for result in results:
            address = result['geometry']['location']
            print(address['lat'], address['lng'], what)
            marker_data.append({'latitude' : address['lat'], 'longitude': address['lng'], 'what' : what, 'link':link})
    
    return jsonify(marker_data)
    
@app.route('/update_WHOnews')
def update_WHOnews():
    con = sqlite3.connect(DB_WHOnews, isolation_level=None)
    cursor = con.cursor()
    cursor.execute('select link from ExternalNews order by id asc limit 1')
    link = cursor.fetchone()

    print(link)
    return jsonify({'link' : link})


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
    os.chdir("project1/buttonupdate")
    with app.app_context():
        db.create_all()
    create_table()
    app.run(host='localhost', port=8023)