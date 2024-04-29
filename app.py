from flask import Flask, request, abort
import requests
import statistics
import os
import requests
# from bs4 import BeautifulSoup
import json
import pandas as pd
import matplotlib.pyplot as plt
from prettytable import PrettyTable 
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage,
    PostbackEvent, MemberJoinedEvent, LocationMessage
)

app = Flask(__name__)

# Channel Access Token and Secret (Note: These should ideally be stored securely, not hardcoded)
access_token = 'uyT/wIyH6kkz35o7X7G8Edzgisq8l4Vn1wTvz+QMXcuKAnaXUhYucEHjaZKRXgAVnYvk3DfMhcsF60/iA6NxzaKgo0SPOb/yn7xLZxmTfzegtqB2J1na74r8SAo2aZCuBsw/+pdnfCLolxSvvD+6lwdB04t89/1O/w1cDnyilFU='
channel_secret = 'fed72a71f8981ef1dec1e5867df85909'
line_bot_api = LineBotApi(access_token)
handler = WebhookHandler(channel_secret)

# Weather functions
def current_weather(address):
    city_list, town_list, town_list2 = {}, {}, {}
    msg = '找不到氣象資訊。'
    city = address[:3]
    district = address[3:6]

    def get_data(url):
        data = requests.get(url)
        data_json = data.json()
        station = data_json['records']['Station']
        for i in station:
            city = i['GeoInfo']['CountyName'] # 城市
            town = i['GeoInfo']['TownName'] # 行政區
            prec = check_data(i['WeatherElement']['Now']['Precipitation']) # 即時降雨量
            airtemp = check_data(i['WeatherElement']['AirTemperature']) # 氣溫
            humd = check_data(i['WeatherElement']['AirTemperature']) # 相對溼度
            dailyhigh = check_data(i['WeatherElement']['DailyExtreme']['DailyHigh']['TemperatureInfo']['AirTemperature']) # 當日最高溫
            dailylow = check_data(i['WeatherElement']['DailyExtreme']['DailyLow']['TemperatureInfo']['AirTemperature']) # 當日最低溫
            if town not in town_list:
                town_list[town] = {'prec': prec, 'airtemp': airtemp, 'humd': humd, 
                                    'dailyhigh': dailyhigh, 'dailylow': dailylow}
            if city not in city_list:
                city_list[city] = {'prec': [], 'airtemp': [], 'humd': [],
                                'dailyhigh': [], 'dailylow': []}
            city_list[city]['prec'].append(prec)
            city_list[city]['airtemp'].append(airtemp)
            city_list[city]['humd'].append(humd)
            city_list[city]['dailyhigh'].append(dailyhigh)
            city_list[city]['dailylow'].append(dailylow)
        return city_list

    # 如果數值小於0，回傳False
    def check_data(e):
        return False if float(e) < 0 else float(e)

    # 產生回傳訊息
    def msg_content(loc, msg):
        for i in loc:
            if i in address: # 如果地址裡存在 key 的名稱
                airtemp = f"氣溫 {loc[i]['airtemp']} 度，" if loc[i]['airtemp'] != False else ''
                humd = f"相對濕度 {loc[i]['humd']}%，" if loc[i]['humd'] != False else ''
                prec = f"累積雨量 {loc[i]['prec']}mm" if loc[i]['prec'] != False else ''
                description = f'{airtemp}{humd}{prec}'.strip('，')
                a = f'{description}。' # 取出 key 的內容作為回傳訊息使用
                break
        return a
    
    try:
        code = 'CWA-371EFA85-E086-45AE-B068-E449E4478D6A'
        url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization={code}&format=JSON'
        get_data(url)

        for i in city_list:
            if i not in town_list2: # 將主要縣市裡的數值平均後，以主要縣市名稱為 key，再度儲存一次，如果找不到鄉鎮區域，就使用平均數值
                town_list2[i] = {'airtemp':round(statistics.mean(city_list[i]['airtemp']),1), 
                                'humd':round(statistics.mean(city_list[i]['humd']),1), 
                                'prec':round(statistics.mean(city_list[i]['prec']),1)
                                }
        msg = msg_content(town_list2, msg)  # 將訊息改為「大縣市」 
        msg = msg_content(town_list[district], msg)   # 將訊息改為「鄉鎮區域」 
        return msg    # 回傳 msg
    except:
        return msg
            
# 氣象預報函式
def forecast(address):
    area_list = {}
    # 將主要縣市個別的 JSON 代碼列出
    json_api = {"宜蘭縣":"F-D0047-001","桃園市":"F-D0047-005","新竹縣":"F-D0047-009","苗栗縣":"F-D0047-013",
            "彰化縣":"F-D0047-017","南投縣":"F-D0047-021","雲林縣":"F-D0047-025","嘉義縣":"F-D0047-029",
            "屏東縣":"F-D0047-033","臺東縣":"F-D0047-037","花蓮縣":"F-D0047-041","澎湖縣":"F-D0047-045",
            "基隆市":"F-D0047-049","新竹市":"F-D0047-053","嘉義市":"F-D0047-057","臺北市":"F-D0047-061",
            "高雄市":"F-D0047-065","新北市":"F-D0047-069","臺中市":"F-D0047-073","臺南市":"F-D0047-077",
            "連江縣":"F-D0047-081","金門縣":"F-D0047-085"}
    msg = '找不到天氣預報資訊。'    # 預設回傳訊息
    try:
        code = 'CWA-371EFA85-E086-45AE-B068-E449E4478D6A'
        url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={code}&format=JSON'
        f_data = requests.get(url)   # 取得主要縣市預報資料
        f_data_json = f_data.json()  # json 格式化訊息內容
        location = f_data_json['records']['location']  # 取得縣市的預報內容
        for i in location:
            city = i['locationName']    # 縣市名稱
            wx8 = i['weatherElement'][0]['time'][0]['parameter']['parameterName']    # 天氣現象
            mint8 = i['weatherElement'][1]['time'][0]['parameter']['parameterName']  # 最低溫
            maxt8 = i['weatherElement'][2]['time'][0]['parameter']['parameterName']  # 最高溫
            pop8 = i['weatherElement'][2]['time'][0]['parameter']['parameterName']   # 降雨機率
            area_list[city] = f'未來 8 小時{wx8}，最高溫 {maxt8} 度，最低溫 {mint8} 度，降雨機率 {pop8} %'  # 組合成回傳的訊息，存在以縣市名稱為 key 的字典檔裡
        for i in area_list:
            if i in address:        # 如果使用者的地址包含縣市名稱
                msg = area_list[i]  # 將 msg 換成對應的預報資訊
                # 將進一步的預報網址換成對應的預報網址
                url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/{json_api[i]}?Authorization={code}&elementName=WeatherDescription'
                f_data = requests.get(url)  # 取得主要縣市裡各個區域鄉鎮的氣象預報
                f_data_json = f_data.json() # json 格式化訊息內容
                location = f_data_json['records']['locations'][0]['location']    # 取得預報內容
                break
        for i in location:
            city = i['locationName']   # 取得縣市名稱
            wd = i['weatherElement'][0]['time'][1]['elementValue'][0]['value']  # 綜合描述
            if city in address:           # 如果使用者的地址包含鄉鎮區域名稱
                msg = f'未來八小時天氣{wd}' # 將 msg 換成對應的預報資訊
                break
        return msg  # 回傳 msg
    except:
        return msg  # 如果取資料有發生錯誤，直接回傳 msg

# 天氣警報
def warning(address):
    area_list = {}
    # 將主要縣市個別的 JSON 代碼列出
    json_api = {"宜蘭縣":"F-D0047-001","桃園市":"F-D0047-005","新竹縣":"F-D0047-009","苗栗縣":"F-D0047-013",
            "彰化縣":"F-D0047-017","南投縣":"F-D0047-021","雲林縣":"F-D0047-025","嘉義縣":"F-D0047-029",
            "屏東縣":"F-D0047-033","臺東縣":"F-D0047-037","花蓮縣":"F-D0047-041","澎湖縣":"F-D0047-045",
            "基隆市":"F-D0047-049","新竹市":"F-D0047-053","嘉義市":"F-D0047-057","臺北市":"F-D0047-061",
            "高雄市":"F-D0047-065","新北市":"F-D0047-069","臺中市":"F-D0047-073","臺南市":"F-D0047-077",
            "連江縣":"F-D0047-081","金門縣":"F-D0047-085"}
    msg = '找不到天氣預報資訊。'    # 預設回傳訊息
    try:
        code = 'CWA-371EFA85-E086-45AE-B068-E449E4478D6A'
        warning_url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/W-C0033-001?Authorization={code}&format=JSON'
        f_data = requests.get(warning_url)   # 取得主要縣市預報資料
        f_data_json = f_data.json()  # json 格式化訊息內容
        location = f_data_json['records']['location']  # 取得縣市的預報內容
        for i in location:
            city = i['locationName']    # 縣市名稱
            warning = i['hazardConditions']['hazards'] # 警報
            area_list[city] = f'即時天氣警報 {warning}'  # 組合成回傳的訊息，存在以縣市名稱為 key 的字典檔裡
        for i in area_list:
            if i in address:        # 如果使用者的地址包含縣市名稱
                msg = area_list[i]  # 將 msg 換成對應的預報資訊
        if not warning:
          msg = '目前未有任何天氣警報'
        return msg
    except:
        return msg  # 如果取資料有發生錯誤，直接回傳 msg

# 溫度分布圖
def reply_temperature_image(reply_token):
    try:
        air_temp_url = 'https://cwaopendata.s3.ap-northeast-1.amazonaws.com/Observation/O-A0038-001.jpg'
        
        line_bot_api.reply_message(
            reply_token,
            ImageSendMessage(
                original_content_url = air_temp_url,
                preview_image_url = air_temp_url
            )
        )
    except Exception as e:
        print(f"Error replying with temperature image: {e}")

# 雷達回波圖
def reply_weather_image(reply_token):
    try:
        radar_url = 'https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/O-A0058-003?Authorization=rdec-key-123-45678-011121314&format=JSON'
        radar = requests.get(radar_url)
        radar_json = radar.json()
        radar_img = radar_json['cwaopendata']['dataset']['resource']['ProductURL']
        radar_time = radar_json['cwaopendata']['dataset']['DateTime']

        line_bot_api.reply_message(
            reply_token,
            ImageSendMessage(
                original_content_url=radar_img,
                preview_image_url=radar_img
            )
        )
    except Exception as e:
        print(f"Error replying with weather image: {e}")

# 未來一週氣象預報
def weekly_weather_forecast_data():
    try:
        url = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091?Authorization=CWA-371EFA85-E086-45AE-B068-E449E4478D6A&format=JSON'
        r = requests.get(url)
        # Parse
        data = pd.read_json(r.text)
        data = data.loc['locations', 'records']
        data = data[0]['location']
        
        aggregated_data = {
            'PoP12h': {}, # 未來12小時降雨機率
            'T': {}, # 平均溫度
            'MaxT': {}, # 最高溫度
            'MinT': {} # 最低溫度
        }
        element_lists = [i for i in aggregated_data.keys()]
        for loc_data in data:
            loc_name = loc_data['locationName'] # 縣市
            weather_data = loc_data['weatherElement'] # 項目
            for element in weather_data:
              ele_name = element['elementName']
              if ele_name in element_lists:
                for entry in element['time']:
                  start_time = entry['startTime'][:10]  # Extract the date
                  value = entry['elementValue'][0]['value']
                  if value.strip():  # Check if value is not empty
                    value = float(value)
                  else:
                    value = 0.0
                  # Store the value for each location, weather element, and start time
                  if start_time not in aggregated_data[ele_name]:
                    aggregated_data[ele_name][start_time] = {}
                  if loc_name not in aggregated_data[ele_name][start_time]:
                    aggregated_data[ele_name][start_time][loc_name] = 0.0
                  aggregated_data[ele_name][start_time][loc_name] += value
                    
        # Divide each value by 2 after all values have been added
        for ele_name in aggregated_data:
            for start_time in aggregated_data[ele_name]:
              for loc_name in aggregated_data[ele_name][start_time]:
                aggregated_data[ele_name][start_time][loc_name] /= 2   
        
        return aggregated_data

    except Exception as e:
        print(e)

def weather_forecast_description(weekly_weather_forecast_data, address):
    try:
        location = address[:3]
        bundles = {
            'PoP12h': [],
            'T': [],
            'MaxT': [],
            'MinT': []
        }
        date_lists = []
    
        for i in bundles.keys():
            for element, location_data in aggregated_data.items():
                if element == i:
                    for date, info in location_data.items():
                        value = info[location]
                        bundles[element].append(value)
                        if date not in date_lists:
                            date_lists.append(date)
    
        df = pd.DataFrame(bundles)
        df['Date'] = pd.to_datetime(date_lists)
        df.set_index('Date', inplace=True)

        # Find the maximum value for PoP12h
        pop_max = df['PoP12h'].max()
        pop_maxidx = df['PoP12h'].idxmax()
        # Extract Unix timestamp from the timestamp object
        pop_maxidx_unix = pop_maxidx.timestamp()
        pop_maxidx_dt = datetime.fromtimestamp(pop_maxidx_unix)
        pop_month = pop_maxidx_dt.month
        pop_day = pop_maxidx_dt.day

        # Find the maximum value for T
        T_max = df['T'].max()
        T_maxidx = df['T'].idxmax()
        # Extract Unix timestamp from the timestamp object
        T_maxidx_unix = T_maxidx.timestamp()
        T_maxidx_dt = datetime.fromtimestamp(T_maxidx_unix)
        maxT_month = T_maxidx_dt.month
        maxT_day = T_maxidx_dt.day
        # Celsius symbol
        celsius_symbol = '\u00B0C'
        maxT_message = f'未來1週最高氣溫預計發生於{maxT_month}/{maxT_date}達{T_max}{celsius_symbol}，'

        # Find the minimum value for MinT
        T_min = df['MinT'].min()
        T_minidx = df['MinT'].idxmin()
        T_minidx_unix = T_minidx.timestamp()
        T_minidx_dt = datetime.fromtimestamp(T_minidx_unix)
        minT_month = T_minidx_dt.month
        minT_day = T_minidx_dt.day
        minT_message = f'未來1週最低氣溫預計發生於{minT_month}/{minT_day}達{T_min}{celsius_symbol}，'

        # Calculate for average temperature
        ave_t = round(df['T'].mean(), 2)
        ave_message = f'未來1週平均氣溫:{ave_t}{celsius_symbol}，'

        description = f'{ave_message}{maxT_message}{minT_message}{pop_message}'.strip('，')
        return description
            
    except Exception as e:
        return e



# Route for handling webhook callback
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# Message handling
@handler.add(MessageEvent, message=[TextMessage, LocationMessage])
def handle_message(event):
    if event.message.type == 'location':
        address = event.message.address.replace('台', '臺')
        msg = f'{address}\n\n{current_weather(address)}\n\n{forecast(address)}\n\n{warning(address)}\n\n{weather_forecast_description(weekly_weather_forecast_data(), address)}'
        message = TextSendMessage(text=msg)
        line_bot_api.reply_message(event.reply_token, message)    
    elif  event.message.type == 'text':
        msg = event.message.text
        if msg.lower() in ['雷達回波圖', '雷達回波', 'radar']:
            reply_weather_image(event.reply_token)
        # if msg in ['溫度分布', '溫度分布圖', '溫度分佈', '溫度分佈圖']:
        if msg == '溫度分布':
            reply_temperature_image(event.reply_token)
        if msg == '成本效益':
            reply_cost_and_effect(event.reply_token)
        else:
            message = TextSendMessage(text=msg)
            line_bot_api.reply_message(event.reply_token, message)

# Other events handling
@handler.add(PostbackEvent)
def handle_postback(event):
    print(event.postback.data)

@handler.add(MemberJoinedEvent)
def handle_member_join(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'Welcome, {name}!')
    line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
