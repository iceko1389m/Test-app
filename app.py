from flask import Flask, request, jsonify
import sqlite3
import threading
import telebot

BOT_TOKEN = "8528248141:AAHjKBWXN5E7DWmMlCOkEFYB-kL1kyVTwmE"
ADMIN_ID  = "2028533085"

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body>
        <h1>تست دکمه‌ها</h1>
        <div id="page1">
            <button onclick="showPage(2)">برو به صفحه ۲</button>
        </div>
        <div id="page2" style="display:none;">
            <button onclick="showPage(1)">برگشت به صفحه ۱</button>
        </div>
        <script>
            function showPage(num) {
                document.getElementById('page1').style.display = 'none';
                document.getElementById('page2').style.display = 'none';
                document.getElementById('page' + num).style.display = 'block';
            }
        </script>
    </body>
    </html>
    """

def run_bot():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
