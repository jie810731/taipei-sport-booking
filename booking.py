from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import re
from selenium.webdriver.support.ui import Select
from datetime import datetime,timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import os
import pytz
import pause
import time

def wait(book_date):
    book_date_in_date_time = datetime.strptime(book_date, "%Y-%m-%d")
    
    start_book_date = book_date_in_date_time - timedelta(days=14)
    start_book_time = start_book_date.replace(hour=9,minute=59,second=58)
    tw_zone = pytz.timezone('Asia/Taipei')

    tw_start_book_time = tw_zone.localize(start_book_time)
    print(f"can start book time = {tw_start_book_time}")
    pause.until(tw_start_book_time)
    print(f"start process time in utc = {datetime.now()}")

def web_driver_init(): 
    options = Options()

    options.add_argument('--headless')
    options.add_argument("window-size=1440,1900")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('–incognito')


    web_driver = webdriver.Chrome(
        executable_path='/usr/local/bin/chromedriver', chrome_options=options)

    return web_driver

def login(web_driver,member_user_name,member_information):
    web_driver.get("https://sports.tms.gov.tw/member/")

    web_driver.add_cookie({'name':'MemberUserName', 'value':member_user_name})
    web_driver.add_cookie({'name':'MEMBER_INFORMATION', 'value':member_information})


def dashrepl(matchobj):
    return '.{}.'.format(matchobj.group(1))

def select_date(web_driver,book_date):
    end_re_try_time = datetime.now() + timedelta(minutes=5)
    while True:
        try:
            if end_re_try_time < datetime.now():
                print('over try')
                
                return  False
            web_driver.refresh()

            select = Select(web_driver.find_element_by_id('RentalData'))
            select.select_by_value(book_date)
            element = web_driver.find_element_by_id('RentalData')
            web_driver.execute_script("ChangeTimePeriodDate(arguments[0]);", element)

            return True
        except Exception as e:
            print(e)

def select_court(web_driver,court):
    if not court:
        return False
    
    end_re_try_time = datetime.now() + timedelta(minutes=5)
    court_xpath = "//a[@id='SubVenues_{}']".format(court)
    while True:
        try:
            if end_re_try_time < datetime.now():
                print('over try select court')
                
                return  False
            element = web_driver.find_element_by_xpath(court_xpath)
            element.click() 

            return True
        except Exception as e:
            print(e)

def select_time(web_driver,book_date,book_times):
    if not book_date:
        return False
    order_date_dot = book_date.replace("-", ".")
    pattern = r"\.0(\d)\."
    order_date_dot = re.sub(pattern, dashrepl, order_date_dot)

    click_date_id = 'DataPickup.{}'.format(order_date_dot)
 
    end_re_try_time = datetime.now() + timedelta(minutes=5)
    for order_time in book_times:
        if not order_time:
            continue

        xpath = "//td[@id='{}.{}.1']//div".format(click_date_id,order_time)

        while True:
            try:
                if end_re_try_time < datetime.now():
                    print('over try select court')
                
                    return  False
                element = web_driver.find_element_by_xpath(xpath)
                web_driver.execute_script("mmDataPickup.Booking(arguments[0],event);", element)
                
                break
            except Exception as e:
                print(e)

    return True

def select_rest(web_driver):
    end_re_try_time = datetime.now() + timedelta(minutes=5)

    element = web_driver.find_element_by_id('ParticipateTypeG')
    element.clear()
    element.send_keys('2')

    # 下一步,送出零租場地
    button = web_driver.find_element_by_xpath("//button[@class='Btn Send']")
    web_driver.execute_script('ChkStep1()',button)

    # dailog 再次確認
    try:
        x_path = "//div[@class='Item']/button[@name='Send']"
        WebDriverWait(web_driver, 5).until(
            expected_conditions.presence_of_element_located((By.XPATH, x_path))
        )

        element = web_driver.find_element_by_xpath(x_path)
        element.click() 

    except TimeoutException:
        print("confirm again, {} element timeout exception".format(x_path))
        web_driver.save_screenshot("confirm_again_exception.png")

        return False
    print('select page finish')
            
    # 我同意
    web_driver.find_element_by_id("Agree").click()
    

    # 下一步,成立零租租借單
    web_driver.execute_script('CreateOrderConfirm()')


    # 請您確認送出訂單
    try:
        x_path = "//div[@class='Item']/button[@name='Send']"
        WebDriverWait(web_driver, 5).until(
            expected_conditions.presence_of_element_located((By.XPATH, x_path))
        )

        element = web_driver.find_element_by_xpath(x_path)
        element.click() 

    except TimeoutException:
        print("send order timeout, {} element timeout exception".format(x_path))
        web_driver.save_screenshot("send_order_exception.png")

        return False
    print('order finish')

def booking_process(web_driver,book_date,book_times,court):
    web_driver.get("https://sports.tms.gov.tw/order_rental/?K=49")
    is_date_continue = select_date(web_driver,book_date)
    print("select date finish")
    if not is_date_continue:
        print("select_date fail")
        return
    is_court_continue = select_court(web_driver,court)
    print("select court finish")

    if not is_court_continue:
        print("select_court fail")
        return

    is_time_continue = select_time(web_driver,book_date,book_times)
    print("select time finish")
    if not is_time_continue:
        print("select_time fail")
        return

    select_rest(web_driver)


if __name__ == '__main__':
    member_user_name = os.environ.get('MEMBER_USER_NAME')
    member_information = os.environ.get('MEMBER_INFORMATION')

    if not member_user_name or not member_information:
        print("missing require")
        quit()
    book_date = os.environ.get('BOOK_DATE')
    book_time = os.environ.get('BOOK_TIME')
    book_times = book_time.split(',')
    court = os.environ.get('COURT')
    if not court:
        court = 736
    print(f"book date = {book_date}")
    print(f"book time = {book_times}")
    print(f"book court = {court}")
    try:
        web_driver = web_driver_init()
        login(web_driver,member_user_name,member_information)
        wait(book_date)
        booking_process(web_driver,book_date,book_times,court)
    except Exception as e:
        print("outer cache exception = {}".format(e))
    
    web_driver.quit()
