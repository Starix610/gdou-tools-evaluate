from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

browser = webdriver.Chrome("chromedriver.exe")
browser.get('https://jw.gdou.edu.cn')

WebDriverWait(browser, 60*60*24).until(EC.presence_of_all_elements_located((By.ID, "myDiv1")), message='用户未登录')