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

# 氣象功能
def reply_weather_image(reply_token):
    image_url = 'https://cwbopendata.s3.ap-northeast-1.amazonaws.com/MSC/O-A0058-003.png'
    line_bot_api.reply_message(
        reply_token,
        ImageSendMessage(
            original_content_url = image_url,
            preview_image_url = image_url
        )
    )

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg= event.message.text
    if msg == '雷達回波圖' or msg == '雷達回波':
        reply_weather_image(event.reply_token)
    else:
        message = TextSendMessage(text=msg)
        line_bot_api.reply_message(event.reply_token, message)

    # message = TextSendMessage(text=msg)
    # line_bot_api.reply_message(event.reply_token,message)
    
    # if '最新合作廠商' in msg:
    #     message = imagemap_message()
    #     line_bot_api.reply_message(event.reply_token, message)
    # elif '最新活動訊息' in msg:
    #     message = buttons_message()
    #     line_bot_api.reply_message(event.reply_token, message)
    # elif '註冊會員' in msg:
    #     message = Confirm_Template()
    #     line_bot_api.reply_message(event.reply_token, message)
    # elif '旋轉木馬' in msg:
    #     message = Carousel_Template()
    #     line_bot_api.reply_message(event.reply_token, message)
    # elif '圖片畫廊' in msg:
    #     message = test()
    #     line_bot_api.reply_message(event.reply_token, message)
    # elif '功能列表' in msg:
    #     message = function_list()
    #     line_bot_api.reply_message(event.reply_token, message)
    # else:
    #     message = TextSendMessage(text=msg)
    #     line_bot_api.reply_message(event.reply_token, message)

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

#LINE_CHANNEL_ACCESS_TOKEN = 'uyT/wIyH6kkz35o7X7G8Edzgisq8l4Vn1wTvz+QMXcuKAnaXUhYucEHjaZKRXgAVnYvk3DfMhcsF60/iA6NxzaKgo0SPOb/yn7xLZxmTfzegtqB2J1na74r8SAo2aZCuBsw/+pdnfCLolxSvvD+6lwdB04t89/1O/w1cDnyilFU='

#token = LINE_CHANNEL_ACCESS_TOKEN

#Authorization_token = "Bearer " + LINE_CHANNEL_ACCESS_TOKEN

# headers = {"Authorization":Authorization_token, "Content-Type":"application/json"}

# body = {
#     "size": {"width": 2500, "height": 843},
#     "selected": "true",
#     "name": "Menu",
#     "chatBarText": "更多資訊",
#     'areas': [
#         {
#             'bounds': {'x': 0, 'y': 0, 'width': 833, 'height': 843},
#             'action': {"type": "message", "text": "以下網站提供了各種氣候變遷相關資訊，可供您參考: \n 1.https://www.ipcc.ch/ \n 2.https://www.climatecentral.org/ \n 3.https://unfccc.int/"}  # Make sure this text is properly encoded
#         },
#         {
#             'bounds': {'x': 833, 'y': 0, 'width': 833, 'height': 843},
#             'action': {'type': 'uri', 'uri': 'https://www.climatecentral.org/'}
#         },
#         {
#             'bounds': {'x': 1666, 'y': 0, 'width': 833, 'height': 843},
#             'action': {"type": "message", "text": "成本效益"}  # Make sure this text is properly encoded
#         }
#     ]
#   }

# req = requests.request('POST', 'https://api.line.me/v2/bot/richmenu',
#                        headers=headers,data=json.dumps(body).encode('utf-8'))

# print(req.text)

# from linebot import (
#     LineBotApi, WebhookHandler
# )

# line_bot_api = LineBotApi(token)
# rich_menu_id = "richmenu-e52c01ced9f0573a185bb55f1df21c2e" # 設定成我們的 Rich Menu ID

# path = "/content/drive/My Drive/linebot_menu.png" # 主選單的照片路徑

# with open(path, 'rb') as f:
#     line_bot_api.set_rich_menu_image(rich_menu_id, "image/png", f)

# req = requests.request('POST', 'https://api.line.me/v2/bot/user/all/richmenu/'+rich_menu_id,
#                        headers=headers)
# print(req.text)

# rich_menu_list = line_bot_api.get_rich_menu_list()
