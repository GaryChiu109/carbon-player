from flask import Flask, request, abort
import requests
import statistics
import os

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage,
    PostbackEvent, MemberJoinedEvent
)

app = Flask(__name__)

# Channel Access Token and Secret (Note: These should ideally be stored securely, not hardcoded)
access_token = 'uyT/wIyH6kkz35o7X7G8Edzgisq8l4Vn1wTvz+QMXcuKAnaXUhYucEHjaZKRXgAVnYvk3DfMhcsF60/iA6NxzaKgo0SPOb/yn7xLZxmTfzegtqB2J1na74r8SAo2aZCuBsw/+pdnfCLolxSvvD+6lwdB04t89/1O/w1cDnyilFU='
channel_secret = 'fed72a71f8981ef1dec1e5867df85909'
line_bot_api = LineBotApi(access_token)
handler = WebhookHandler(channel_secret)

# Utility functions
def get_data(url):
    """Fetches data from the given URL and returns JSON."""
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.json()

def check_data(value):
    """Checks if the given value is valid (not negative) and returns it."""
    return float(value) if float(value) >= 0 else None

# Weather functions
def current_weather(address):
    """Returns the current weather information for the given address."""
    city_list, area_list, area_list2 = {}, {}, {}
    msg = 'No weather information available.'

    try:
        code = 'CWA-371EFA85-E086-45AE-B068-E449E4478D6A'
        data_urls = [
            f'https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/O-A0001-001?Authorization={code}&downloadType=WEB&format=JSON',
            f'https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/O-A0003-001?Authorization={code}&downloadType=WEB&format=JSON'
        ]

        for url in data_urls:
            w_data_json = get_data(url)
            location = w_data_json['cwbopendata']['location']
            for item in location:
                name = item['locationName']
                city = item['parameter'][0]['parameterValue']
                area = item['parameter'][2]['parameterValue']
                temp = check_data(item['weatherElement'][3]['elementValue']['value'])
                humd = check_data(round(float(item['weatherElement'][4]['elementValue']['value']) * 100, 1))
                r24 = check_data(item['weatherElement'][6]['elementValue']['value'])

                area_list.setdefault(area, {'temp': temp, 'humd': humd, 'r24': r24})
                city_list.setdefault(city, {'temp': [], 'humd': [], 'r24': []})
                city_list[city]['temp'].append(temp)
                city_list[city]['humd'].append(humd)
                city_list[city]['r24'].append(r24)

        for city, data in city_list.items():
            area_list2[city] = {
                'temp': round(statistics.mean(data['temp']), 1),
                'humd': round(statistics.mean(data['humd']), 1),
                'r24': round(statistics.mean(data['r24']), 1)
            }

        msg = format_weather_message(area_list2, msg)
        msg = format_weather_message(area_list, msg)
    except Exception as e:
        print(f"Error fetching weather data: {e}")

    return msg

def format_weather_message(locations, default_msg):
    """Formats the weather message based on the locations data."""
    formatted_msg = default_msg
    for location, data in locations.items():
        if location in address:
            temp_str = f"Temperature: {data['temp']}°C, " if data['temp'] is not None else ''
            humd_str = f"Humidity: {data['humd']}%, " if data['humd'] is not None else ''
            r24_str = f"Rainfall: {data['r24']}mm" if data['r24'] is not None else ''
            description = f'{temp_str}{humd_str}{r24_str}'.strip(', ')
            formatted_msg = f'{description}.'
            break
    return formatted_msg

def reply_weather_image(reply_token):
    """Replies with the latest weather radar image."""
    try:
        radar_url = 'https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/O-A0058-003?Authorization=rdec-key-123-45678-011121314&format=JSON'
        radar_json = get_data(radar_url)
        radar_img = radar_json['cwaopendata']['dataset']['resource']['ProductURL']

        line_bot_api.reply_message(
            reply_token,
            ImageSendMessage(
                original_content_url=radar_img,
                preview_image_url=radar_img
            )
        )
    except Exception as e:
        print(f"Error replying with weather image: {e}")

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
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print(event)
    msg = event.message.text
    if msg.lower() in ['雷達回波圖', '雷達回波', 'radar']:
        reply_weather_image(event.reply_token)
    elif '台' in msg or '臺' in msg:
        weather_forecast = current_weather(msg)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=weather_forecast))
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
