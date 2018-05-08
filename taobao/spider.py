from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
import re
from bs4 import BeautifulSoup as bs
from config import *
from pymongo import MongoClient
from time import time

client = MongoClient(Mongodb_url, Mongodb_port)
db = client[Db_name]
browser = webdriver.Chrome()
wait = WebDriverWait(browser, 10)

#
def search_keyword(keywords):
    '''搜索关键字并返回总页数'''
    try:
        browser.get("https://www.taobao.com")
        input_area = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#q")) #等待元素加载
        )
        button = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#J_TSearchForm > div.search-button > button"))
        )
        input_area.clear()  # 清除原字符
        input_area.send_keys(keywords)
        button.click()
        page_sum = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.total"))
        )
        # 提取数字
        page_sum = int(re.compile(r"(\d+)").findall(page_sum.text)[0])
        get_infomation()
        return page_sum
    except TimeoutException:
        search_keyword(keywords)

def next_page(page_index):
    '''实现翻页'''
    try:
        input_area = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > input"))
        )
        submit = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit"))
        )
        input_area.clear()  # 清除原字符
        input_area.send_keys(page_index)
        submit.click()
        # 等待当前页加载完
        wait.until(EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR,"#mainsrp-pager > div > div > div > ul > li.item.active > span"),str(page_index))
        )
        get_infomation()    # 获取当前页信息
    except TimeoutException:
        next_page(page_index)

def get_infomation():
    # 加载成功
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR,"#mainsrp-itemlist .items .item"))
    )
    soup = bs(browser.page_source,"lxml")
    items = soup.select("#mainsrp-itemlist .items .item")   # 选中所有商品
    for item in items:# 逐个保存
        information = {
            "image":item.select_one(".pic .img")["src"],
            "price":item.select(".price")[0].get_text(strip=True),
            "deal-cnt":item.select(".deal-cnt")[0].get_text(strip=True)[:-3],
            "title":item.select(".row.title")[0].get_text(strip=True),
            "shop":item.select(".shop")[0].get_text(strip=True),
            "location":item.select(".location")[0].get_text(strip=True)
        }
        save_to_mongodb(information)

def save_to_mongodb(information):
    try:
        if db[Db_table].save(information):
            print("保存成功",information)
    except Exception:
        print("------>保存出错！",information)

def main():
    page_nums = search_keyword(Keywords)
    print("共计 %d 页"%page_nums)
    for page_index in range(2,page_nums+1):
        print("第 %d 页"%page_index)
        next_page(page_index)


if __name__ == "__main__":
    start = time()
    main()
    end = time()
    print("共耗时 %3f"%(end-start))