from flask import Flask, request, abort
import requests
import statistics
import os
import requests
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
        msg = f'{address}\n\n{current_weather(address)}\n\n{forecast(address)}\n\n{warning(address)}'
        message = TextSendMessage(text=msg)
        line_bot_api.reply_message(event.reply_token, message)    
    elif  event.message.type == 'text':
        msg = event.message.text
        if msg.lower() in ['雷達回波圖', '雷達回波', 'radar']:
            reply_weather_image(event.reply_token)
        # if msg in ['溫度分布', '溫度分布圖', '溫度分佈', '溫度分佈圖']:
        if msg == '溫度分布':
            reply_temperature_image(event.reply_token)
        else:
            message = TextSendMessage(text=msg)
            line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
