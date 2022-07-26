import requests
import json
import os
import datetime
import pause
from datetime import datetime,timedelta
import pytz
from bs4 import BeautifulSoup
import html

def wait(book_date):
    book_date_in_date_time = datetime.strptime(book_date, "%Y-%m-%d")
    
    start_book_date = book_date_in_date_time - timedelta(days=14)
    start_book_time = start_book_date.replace(hour=10,minute=0,second=0)
    tw_zone = pytz.timezone('Asia/Taipei')

    tw_start_book_time = tw_zone.localize(start_book_time)
    print(f"can start book time = {tw_start_book_time}")
    pause.until(tw_start_book_time)
    print(f"start process time in utc = {datetime.now()}")

def getCourtCode(court_number):
    mapping = {
        '01':'727',
        '02':'728',
        '03':'729',
        '04':'730',
        '05':'731',
        '06':'732',
        '07':'733',
        '08':'734',
        '09':'735',
        '10':'736'
    }

    return mapping[court_number]

def getData(year,month,court):
    session_id = getSessionId()
    cookies = {'PHPSESSID': session_id}
    pload = {
        'FUNC':'LoadSched',
        'SY':year,
        'SM':month,
        'VenueSN':court,
    }
    print(cookies)
    r = requests.post('https://sports.tms.gov.tw/_/x/xhrworkv3.php',data = pload,cookies=cookies)

    return r.json()

def getTimePeriod(book_date,book_times,court):
    time_period = {}
    date_object = datetime.strptime(book_date, '%Y-%m-%d')
    schedul = getData(date_object.year,date_object.month,court)
    for book_time in book_times:
        time_detail = schedul['RT'][str(date_object.day)]["{}00".format(book_time)]
        time_period[time_detail['K']] = {
            'RentDate':book_date,
            "StartTime": "{}:00".format(time_detail['S']),
            "EndTime": "{}:00".format(time_detail['E']),
            "VenuesSN": time_detail['V']
        }
    
    return time_period

def getTotalFeed(book_times):
    total_feed = 0
    for book_time in book_times :
        if int(book_time) < 10:
            total_feed += 150

            continue
        if int(book_time) < 18:
            total_feed += 300

            continue
        
        total_feed += 500

    return str(total_feed)

def getSessionId():
    session = requests.Session()
    while True:
        response = session.get('https://sports.tms.gov.tw/venues/?K=49')
        if response.status_code == 200:
            break

    return session.cookies.get_dict()['PHPSESSID']

def covertStrintToLocalDateTime(time):
    time_object = datetime.strptime(book_date, "%Y-%m-%d")
    tw_zone = pytz.timezone('Asia/Taipei')

    tw_time_object = tw_zone.localize(time_object)
    
    return tw_time_object

def getSessionTime(book_date_time_object):
    mytime = book_date_time_object - timedelta(days=14)
    start_mytime = mytime.replace(hour=9,minute=59,second=50)

    return start_mytime

def getStartBookTime(book_date_time_object):
    mytime = book_date_time_object - timedelta(days=14)
    start_mytime = mytime.replace(hour=10,minute=00,second=00)

    return start_mytime

def book(files,cookies):
    while True:
        try:
            edit_request = requests.post('https://sports.tms.gov.tw/order_rental/?U=venue&K=49', files=files,cookies=cookies , timeout=5)
        
            if edit_request.status_code == 200:
                break
        except Exception as e:
            print(e)

    print(f"finish edit request time in utc = {datetime.now()}")

    data = {
        "TopVenueSn": "1",
        "Agree": "1",
        "SendView": "OK"
    }

    while True:
        try:
            send_request = requests.post('https://sports.tms.gov.tw/order_rental/?U=view', data=data,cookies=cookies , timeout=5)
            if send_request.status_code == 200:
                break
        except Exception as e:
            print(e)
    
    print(f"finish send request time in utc = {datetime.now()}")

def checkOrder(cookies,book_date,book_times ,court):
    is_order = False

    orderResponse = requests.post('https://sports.tms.gov.tw/member/?U=rental',cookies=cookies)
    # responseString = html.unescape(orderResponse.content) 
    soup = BeautifulSoup(orderResponse.content, 'html.parser')

    tbodies = soup.find_all("tbody","ItemTbody")

    for tbody in tbodies:
        td = tbody.contents[1].contents[9]

        orderCourt = next(td.contents[0].stripped_strings)
        orderCourt = str([int(x) for x in orderCourt if x.isdigit()][0])
        orderCourt = orderCourt.zfill(2)

        if orderCourt != court:
            continue

        timesDivs = td.contents[1].find_all("div")
        
        bookDate = ''
        bookTimes = []
        for index,div in enumerate(timesDivs):
            if index == 0:
                bookDate = div.contents[0].string
                
                continue
            
            time = div.contents[0].string
            time = time[ 0 : 2 ]

            bookTimes.append(time)
        
        if bookDate != book_date:
            continue

        for item in  bookTimes:
            if item in book_times:
                is_order = True
                break
        
        if is_order == True:
            break
    
    return is_order

if __name__ == '__main__':
    book_date = os.environ['BOOK_DATE']
    book_time = os.environ['BOOK_TIME']
    book_times = book_time.split(',')
    court_number = os.environ.get('COURT_NUMBER')
    member_information = os.environ['MEMBER_INFORMATION']

    court = getCourtCode(court_number)
    time_period = getTimePeriod(book_date,book_times,court)    
    total_feed = getTotalFeed(book_times)

    book_date_time_object = covertStrintToLocalDateTime(book_date)
    get_session_time = getSessionTime(book_date_time_object)
    get_start_book_time = getStartBookTime(book_date_time_object)


    files={
        'TopVenueSn': (None, '1'), 
        'VenueSn': (None, '49'),
        'ZRLimitHR': (None, ''),
        'TimePeriod': (None, json.dumps(time_period)),
        'SubVenues': (None, court),
        'ParticipateTypeG': (None, '1'),
        'ParticipateTypeP': (None, '0'),
        'ZRentalInfo': (None, json.dumps({"未優惠":{"Hour":len(book_times)}})),
        'VenueFeesCost': (None, total_feed),
        'MonthlyTicketCost': (None, '0'),
        'VenueTotalCost': (None, total_feed),
        'MaxMarginCost': (None, '0'),
        'MaxDepositCost': (None, '0'),
        'AllTotalCost': (None, total_feed),
        'SendVenue': (None, 'OK')
    }

    pause.until(get_session_time)

    print(f"start get session time in utc = {datetime.now()}")

    session_id = getSessionId()
    
    print(f"finish get session time in utc = {datetime.now()}")

    cookies = {
        "PHPSESSID": session_id, 
        "MEMBER_INFORMATION": member_information
        }

    pause.until(get_start_book_time)

    end_try_time = datetime.now() + timedelta(minutes=15)

    isOrdered = False
    while not isOrdered :
        if datetime.now() > end_try_time:
            print("over end try time")
            break

        book(files,cookies)

        isOrdered = checkOrder(cookies,book_date,book_times,court_number)

        if not isOrdered:
            print(f"time = {datetime.now()} does not ordered start pause")
            pause.seconds(4)
