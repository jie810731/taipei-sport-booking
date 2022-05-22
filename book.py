import requests
import json
import os
import datetime
import pause
from datetime import datetime,timedelta
import pytz

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
    pload = {
        'FUNC':'LoadSched',
        'SY':year,
        'SM':month,
        'VenueSN':court,
    }
    r = requests.post('https://sports.tms.gov.tw/_/x/xhrworkv3.php',data = pload)

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
    response = session.get('https://sports.tms.gov.tw/member/?U=home')

    return session.cookies.get_dict()['PHPSESSID']


if __name__ == '__main__':
    book_date = os.environ['BOOK_DATE']
    book_time = os.environ['BOOK_TIME']
    book_times = book_time.split(',')
    court_number = os.environ.get('COURT_NUMBER')
    member_information = os.environ['MEMBER_INFORMATION']

    court = getCourtCode(court_number)
    time_period = getTimePeriod(book_date,book_times,court)    
    total_feed = getTotalFeed(book_times)

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

    wait(book_date)

    session_id = getSessionId()
    cookies = {
        "PHPSESSID": session_id, 
        # "MEMBER_INFORMATION":"OB3%2FABV6k%2BFCrB0vFFVquDInTMIiwLILZC4PfKIXe9Y%2FhNFihDInTMIiwB3HlLJ7gKInXBYHYLmzZNI3bN0rVNomu9nHlLJ7gKInXBVjAKInXBgIvdQEsdgQmgFihFY3fLFquCJziN4XVKJDbNorGQJzXBgIyUwEsggICVQQwcFihCJziN4XVKJDbNorGQJzXBVj%2BNoPbNXDbNIGw%2BVyk%2BUmi%2FEmk%2BEyk%2B1ak%2B1am%2FlihF4vZMIrGMInXBVj7L4HgP4XmQHDrO4HFFVqjB0v7L4HgP4XmQHDrO4HFFVquIW3WNIXgBVyu9nbzL4nbNVquFIvUMIjXG4ThNYGw%2B1Wl%2Bl2k%2BlCn%2FVihFIvUMIjXG4ThNYGwB3zaNorXBVyr%2Bl%2Bj%2BV%2Bm%2FFKu9nzaNorXBVj1CIDfMIqw%2B1ihCm3WNIXgBVj1HYHgPIGw%2B1ihCnLXNZHXBVj1CG3WNIXgBVyu9m%2FzCIDfMIqwB2vzL4nbNVqiB0vBCIDfMIqwB2LkLIHsLFtXW8Ku9mLkLIHsLFquDZ7XLJbXGYHTOovgBVihDZ7XLJbXGYHTOovgBVjGKIXiLIXCKJ%2FlEICwB0vGKIXiLIXCKJ%2FlEICwB3DTMJzXMHzTOp%2FEFWX2BVyu9nDTMJzXMHzTOp%2FEFWX2BS"
        "MEMBER_INFORMATION": member_information
        }

    edit_request = requests.post('https://sports.tms.gov.tw/order_rental/?U=venue&K=49', files=files,cookies=cookies)

    print(f"finish edit request time in utc = {datetime.now()}")

    data = {
        "TopVenueSn": "1",
        "Agree": "1",
        "SendView": "OK"
    }
    send_request = requests.post('https://sports.tms.gov.tw/order_rental/?U=view', data=data,cookies=cookies)
    
    print(f"finish send request time in utc = {datetime.now()}")
