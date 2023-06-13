import requests
from bs4 import BeautifulSoup
import sqlite3
from urllib.parse import urljoin

base_url = "https://www.0404.go.kr/dev/newest_list.mofa"

# 데이터베이스 연결
conn = sqlite3.connect('ForSafeTrip.db')
cursor = conn.cursor()

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
for page in range(1, 6):  # 1부터 5까지의 페이지 크롤링
    params = {
        "id": "",
        "pagenum": str(page),
        "mst_id": "MST0000000000041",
        "ctnm": "",
        "div_cd": "",
        "st": "title",
        "stext": ""
    }

    response = requests.get(base_url, params=params)
    soup = BeautifulSoup(response.content, 'html.parser')
    global_news = soup.find_all('td', class_='subject')
    global_countries = soup.find_all('td', class_='bb_ctr1')

    for news, country in zip(global_news, global_countries):
        title = news.text.strip()
        link = news.a

        if link is not None:
            # 자바스크립트 형식의 링크를 URL 형식으로 변환
            link_text = urljoin(base_url, link['href']).replace("javascript:gopage(", "").replace(")", "")
            link_text = f"{base_url}?pagenum={link_text}&mst_id=MST0000000000041"
        else:
            link_text = ""

        country_name = country.text.strip()

        # 데이터 삽입
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
