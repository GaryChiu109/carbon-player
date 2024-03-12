from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *


#======這裡是呼叫的檔案內容=====
from message import *
from new import *
from Function import *
#======這裡是呼叫的檔案內容=====

#======python的函數庫==========
import tempfile, os
import datetime
import time
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi('uyT/wIyH6kkz35o7X7G8Edzgisq8l4Vn1wTvz+QMXcuKAnaXUhYucEHjaZKRXgAVnYvk3DfMhcsF60/iA6NxzaKgo0SPOb/yn7xLZxmTfzegtqB2J1na74r8SAo2aZCuBsw/+pdnfCLolxSvvD+6lwdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('fed72a71f8981ef1dec1e5867df85909')


# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    if '最新合作廠商' in msg:
        message = imagemap_message()
        line_bot_api.reply_message(event.reply_token, message)
    elif '最新活動訊息' in msg:
        message = buttons_message()
        line_bot_api.reply_message(event.reply_token, message)
    elif '註冊會員' in msg:
        message = Confirm_Template()
        line_bot_api.reply_message(event.reply_token, message)
    elif '旋轉木馬' in msg:
        message = Carousel_Template()
        line_bot_api.reply_message(event.reply_token, message)
    elif '圖片畫廊' in msg:
        message = test()
        line_bot_api.reply_message(event.reply_token, message)
    elif '功能列表' in msg:
        message = function_list()
        line_bot_api.reply_message(event.reply_token, message)
    else:
        message = TextSendMessage(text=msg)
        line_bot_api.reply_message(event.reply_token, message)

@handler.add(PostbackEvent)
def handle_message(event):
    print(event.postback.data)


@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)
        
        
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

import requests
import json
# 設定 headers，輸入你的 Access Token，記得前方要加上「Bearer 」( 有一個空白 )
headers = {'Authorization':'Bearer 你的 uyT/wIyH6kkz35o7X7G8Edzgisq8l4Vn1wTvz+QMXcuKAnaXUhYucEHjaZKRXgAVnYvk3DfMhcsF60/iA6NxzaKgo0SPOb/yn7xLZxmTfzegtqB2J1na74r8SAo2aZCuBsw/+pdnfCLolxSvvD+6lwdB04t89/1O/w1cDnyilFU=','Content-Type':'application/json'}

body = {
    'size': {'width': 1080, 'height': 360},   # 設定尺寸
    'selected': 'true',                        # 預設是否顯示
    'name': 'Menu',                   # 選單名稱
    'chatBarText': 'Menu',            # 選單在 LINE 顯示的標題
    'areas':[                                  # 選單內容
        {
          'bounds': {'x': 0, 'y': 720, 'width': 360, 'height': 360}, # 選單位置與大小
          'action': {'type': 'message', 'text': '為您提供氣候變遷資訊 \n '}                # 點擊後傳送文字
        },
        {
          'bounds': {'x': 360, 'y': 720, 'width': 360, 'height': 360},
          'action': {'type': 'uri', 'text': 'https://www.climatecentral.org/'}
        }
    ]
  }
# 向指定網址發送 request
req = requests.request('POST', 'https://api.line.me/v2/bot/richmenu',
                      headers=headers,data=json.dumps(body).encode('utf-8'))
# 印出得到的結果
print(req.text)
