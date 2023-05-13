from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# 웹 페이지 URL
url = 'https://www.safekorea.go.kr/idsiSFK/neo/main/main.html'  # 실제 웹 페이지 URL로 교체해주세요.

# 크롬 웹 드라이버 경로 설정
chrome_driver_path = 'project1/crawling/chromedriver_mac_arm64/chromedriver'  # 실제 Chrome 웹 드라이버 경로로 교체해주세요.

# 옵션 설정 (headless 모드)
chrome_options = Options()
chrome_options.add_argument("--headless")

# 웹 드라이버 실행 및 웹 페이지 로드
driver = webdriver.Chrome(executable_path=chrome_driver_path, options=chrome_options)
driver.get(url)


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

print(str(li_elements[0]))
