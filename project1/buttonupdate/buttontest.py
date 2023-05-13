from flask import Flask, render_template, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# 웹 페이지 URL
url = 'https://www.safekorea.go.kr/idsiSFK/neo/main/main.html' 

# 크롬 웹 드라이버 경로 설정
chrome_driver_path = 'project1/crawling/chromedriver_mac_arm64/chromedriver'  

# 옵션 설정 (headless 모드)
chrome_options = Options()
chrome_options.add_argument("--headless")

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('main.html')

@app.route('/update_content', methods=['POST'])
def update_content():
    

    # 웹 드라이버 실행 및 웹 페이지 로드
    driver = webdriver.Chrome(executable_path=chrome_driver_path, options=chrome_options)
    driver.get(url)

    # 필요한 경우 JavaScript 함수 실행 (예: fn_search())
    #driver.execute_script('fn_search()')

    # 웹 페이지의 변경된 내용 가져오기
    html_content = driver.page_source

    # BeautifulSoup 객체 생성
    soup = BeautifulSoup(html_content, 'html.parser')

    # 'gen' 요소와 하위 'li' 태그 가져오기
    gen_element = soup.find(id='gen')
    li_elements = gen_element.find_all('li')

    # 각 'li' 요소의 HTML 내용 출력
    for li in li_elements:
        print(li)

    # 웹 드라이버 종료
    driver.quit()

    new_content = str(li_elements[0])
    return jsonify({"content": new_content})

if __name__ == "__main__":
    app.run(port=8000)
