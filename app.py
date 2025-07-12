from flask import Flask, request, abort

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessageApiBlob,
    RichMenuSize,
    RichMenuRequest,
    RichMenuArea,
    RichMenuBounds,
    MessageAction,
    ReplyMessageRequest,
    TemplateMessage,
    ButtonsTemplate,
    PostbackAction
)
from linebot.v3.webhooks import (
    MessageEvent,
    FollowEvent,
    PostbackEvent,
    TextMessageContent
)

import requests
import json
import os

app = Flask(__name__)

configuration = Configuration(access_token=os.getenv('CHANNEL_ACCESS_TOKEN'))
line_handler = WebhookHandler(channel_secret=os.getenv('CHANNEL_SECRET'))


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

# Handle follow event
@line_handler.add(FollowEvent)
def handle_follow(event):
    print(f'Got {event.type} event')

@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    print(f"收到訊息：{event.message.text}")  # debug log

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        if event.message.text.lower() == 'postback':
            buttons_template = ButtonsTemplate(
                title='這是一個 Postback 按鈕範例',
                text='請點選下方按鈕',
                actions=[
                    PostbackAction(
                        label='點我回傳 postback',
                        text='你點了按鈕！',
                        data='postback'
                    )
                ]
            )
            template_message = TemplateMessage(
                alt_text='這是一個按鈕訊息',
                template=buttons_template
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[template_message]
                )
            )
        else:
            # fallback 回覆
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[{
                        "type": "text",
                        "text": f"你說的是：{event.message.text}"
                    }]
                )
            )


@line_handler.add(PostbackEvent)
def handle_postback(event):
    print(f"收到 Postback 事件，data: {event.postback.data}")
    if event.postback.data == 'postback':
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[{
                        "type": "text",
                        "text": "你點擊了 Postback 按鈕！"
                    }]
                )
            )

# Create a rich menu
def create_rich_menu_1():
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_blob_api = MessageApiBlob(api_client)
        
        headers ={
            'Authorization': f'Bearer {os.getenv("CHANNEL_ACCESS_TOKEN")}',
            'Content-Type': 'application/json'
        }
        
        body = {
            "size": {
                "width": 2500,
                "height": 1686
            },
            "selected": True,
            "name": "圖文選單 1",
            "chatBarText": "畢聯會小幫手",
            "areas": [
                {
                "bounds": {
                    "x": 0,
                    "y": 0,
                    "width": 833,
                    "height": 843
                },
                "action": {
                    "type": "message",
                    "text": "學位服資訊"
                }
                },
                {
                "bounds": {
                    "x": 833,
                    "y": 0,
                    "width": 833,
                    "height": 843
                },
                "action": {
                    "type": "message",
                    "text": "活動專區"
                }
                },
                {
                "bounds": {
                    "x": 0,
                    "y": 843,
                    "width": 833,
                    "height": 843
                },
                "action": {
                    "type": "message",
                    "text": "畢業典禮"
                }
                },
                {
                "bounds": {
                    "x": 833,
                    "y": 843,
                    "width": 833,
                    "height": 843
                },
                "action": {
                    "type": "uri",
                    "uri": "https://www.instagram.com/ntut_gsa/?__pwa=1"
                }
                }
            ]
            }

        response = requests.post('https://api.line.me/v2/bot/richmenu', headers=headers, data=json.dumps(body).encode('utf-8'))
        response = response.json()
        rich_menu_id = response['richMenuId']
        
        with open('static/richmenu1.jpg', 'rb') as image:
            line_bot_blob_api.set_rich_menu_image(
                rich_menu_id=rich_menu_id,
                body=bytearray(image.read()),
                _headers={
                    'Content-Type': 'image/jpeg'
                }
            )
            
        line_bot_api.set_default_rich_menu(rich_menu_id=rich_menu_id)
        
create_rich_menu_1()

if __name__ == "__main__":
    app.run()