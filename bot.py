import sqlite3
import requests
import threading
import telebot
from flask import Flask, request, jsonify
import os

# ====== تنظیمات ======
BOT_TOKEN = "8528248141:AAHjKBWXN5E7DWmMlCOkEFYB-kL1kyVTwmE"
ADMIN_ID  = "2028533085"
BOT_URL   = "https://t.me/Mahmoudiiiiiii_bot"
BASE_URL  = "https://test-app-abc.onrender.com" # آدرس سایت Render خودت
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
        wallet TEXT,
        balance REAL DEFAULT 0.0,
        status TEXT DEFAULT 'pending',
        referrer TEXT DEFAULT NULL,
        ref_count INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()

init_db()

# ====== ربات تلگرام (پنل ادمین) ======
@bot.message_handler(commands=['start'])
def bot_start(message):
    if str(message.chat.id) == ADMIN_ID:
        bot.reply_to(message, "👑 Admin Panel Active. Use /pending to see new users.")

@bot.message_handler(commands=['pending'])
def bot_pending(message):
    if str(message.chat.id) != ADMIN_ID: return
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT id, email, wallet FROM users WHERE status='pending'")
    users = c.fetchall()
    conn.close()
    
    if not users:
        bot.reply_to(message, "No pending users.")
        return
        
    for u in users:
        uid, email, wallet = u
        text = f"👤 **New Signup**\n\n📧 Email: {email}\n💳 Wallet: {wallet}\n🆔 ID: {uid}"
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{uid}"),
                   telebot.types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{uid}"))
        bot.send_message(ADMIN_ID, text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if str(call.from_user.id) != ADMIN_ID: return
    action, uid = call.data.split('_')
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    
    if action == 'approve':
        c.execute("UPDATE users SET status='approved' WHERE id=?", (uid,))
        c.execute("SELECT referrer FROM users WHERE id=?", (uid,))
        ref = c.fetchone()[0]
        if ref:
            c.execute("UPDATE users SET balance = balance + 1.0, ref_count = ref_count + 1 WHERE email=?", (ref,))
        
        bot.answer_callback_query(call.id, "User Approved!")
        bot.edit_message_text("✅ Approved.", call.message.chat.id, call.message.message_id)
    else:
        c.execute("UPDATE users SET status='rejected' WHERE id=?", (uid,))
        bot.answer_callback_query(call.id, "User Rejected!")
        bot.edit_message_text("❌ Rejected.", call.message.chat.id, call.message.message_id)
        
    conn.commit()
    conn.close()

# ====== وب سرور (بازی) ======
html_game = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>TetherTap</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<style>
  :root {
    --primary: #00ffcc;
    --bg: #0b0f19;
    --card: #151b2b;
    --accent: #ff0055;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
  body { background: var(--bg); color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; overflow: hidden; }
  
  .app-container { width: 100%; max-width: 400px; padding: 20px; text-align: center; position: relative; }
  .screen { display: none; animation: fadeIn 0.4s ease-out; }
  .active { display: block; }
  
  @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
  
  h1 { font-size: 28px; font-weight: 800; background: linear-gradient(90deg, #00ffcc, #00b3ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 5px; }
  p { color: #8892b0; font-size: 14px; margin-bottom: 20px; }
  
  input { width: 100%; padding: 15px; margin-bottom: 15px; border-radius: 12px; border: 1px solid #2a3441; background: var(--card); color: white; font-size: 14px; outline: none; transition: 0.3s; }
  input:focus { border-color: var(--primary); box-shadow: 0 0 10px rgba(0, 255, 204, 0.2); }
  
  button { width: 100%; padding: 16px; background: var(--primary); color: #000; border: none; border-radius: 12px; font-weight: 800; font-size: 16px; cursor: pointer; transition: 0.2s; }
  button:active { transform: scale(0.98); }
  
  .balance-card { background: var(--card); border-radius: 20px; padding: 20px; margin-bottom: 30px; border: 1px solid #2a3441; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
  .balance-value { font-size: 42px; font-weight: 800; color: var(--primary); text-shadow: 0 0 15px rgba(0, 255, 204, 0.4); }
  .balance-label { font-size: 12px; color: #8892b0; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
  
  .tap-area { position: relative; height: 250px; display: flex; justify-content: center; align-items: center; }
  .tap-btn { 
    width: 180px; height: 180px; border-radius: 50%; 
    background: radial-gradient(circle at 30% 30%, #2a3441, #151b2b); 
    border: 4px solid var(--primary); 
    font-size: 80px; display: flex; justify-content: center; align-items: center; 
    cursor: pointer; box-shadow: 0 0 40px rgba(0, 255, 204, 0.2); 
    transition: 0.1s; user-select: none;
  }
  .tap-btn:active { transform: scale(0.9); box-shadow: 0 0 60px rgba(0, 255, 204, 0.5); border-color: white; }
  
  .ref-box { background: var(--card); border-radius: 16px; padding: 20px; margin-top: 20px; border: 1px solid #2a3441; }
  .ref-box h2 { font-size: 16px; margin-bottom: 10px; color: var(--primary); }
  .ref-link { background: #0b0f19; padding: 10px; border-radius: 8px; font-size: 12px; color: #8892b0; margin: 10px 0; word-break: break-all; }
  .ref-stat { display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 10px; color: #ccd6f6; }
</style>
</head>
<body>
<div class="app-container">
  
  <!-- Login Screen -->
  <div id="login-screen" class="screen active">
    <h1>TetherTap</h1>
    <p>Tap to earn USDT. Verify to withdraw.</p>
    <input type="email" id="email" placeholder="Email Address">
    <input type="text" id="wallet" placeholder="USDT Wallet (TRC20)">
    <button onclick="register()">Start Tapping</button>
  </div>

  <!-- Wait Screen -->
  <div id="wait-screen" class="screen">
    <h1>Verifying...</h1>
    <p>Your account is pending admin approval. Please wait.</p>
    <div class="balance-card">
      <div class="balance-label">Status</div>
      <div class="balance-value">⏳</div>
    </div>
  </div>

  <!-- Game Screen -->
  <div id="game-screen" class="screen">
    <div class="balance-card">
      <div class="balance-label">Your Balance</div>
      <div class="balance-value"><span id="balance">0.0000</span> <span style="font-size:20px; color:#fff;">USDT</span></div>
    </div>
    
    <div class="tap-area">
      <div class="tap-btn" onclick="tap()">🪙</div>
    </div>
    
    <div class="ref-box">
      <h2>Invite Friends</h2>
      <div class="ref-stat">
        <span>Friends Invited:</span>
        <span id="ref_count" style="color:var(--primary); font-weight:bold;">0</span>
      </div>
      <p style="margin-bottom:10px; font-size:12px;">Earn 1 USDT per verified friend!</p>
      <div class="ref-link" id="ref_link">loading...</div>
      <button onclick="copyLink()" style="padding: 10px; font-size: 14px;">Copy Invite Link</button>
    </div>
  </div>

</div>

<script>
  let userEmail = "";
  const urlParams = new URLSearchParams(window.location.search);
  const referrer = urlParams.get('ref') || "";

  async function register() {
    const email = document.getElementById('email').value;
    const wallet = document.getElementById('wallet').value;
    if(!email || !wallet) return alert("Please fill all fields");
    
    const res = await fetch('/api/register', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email, wallet, referrer})
    });
    const data = await res.json();
    if(data.success) {
      userEmail = email;
      document.getElementById('login-screen').classList.remove('active');
      document.getElementById('wait-screen').classList.add('active');
      checkStatus();
    } else {
      alert("Registration failed. Email might be in use.");
    }
  }

  async function checkStatus() {
    const res = await fetch('/api/status', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email: userEmail})
    });
    const data = await res.json();
    
    if(data.status === 'approved') {
      document.getElementById('wait-screen').classList.remove('active');
      document.getElementById('game-screen').classList.add('active');
      updateUI(data.balance, data.ref_count);
      
      const baseUrl = window.location.origin;
      document.getElementById('ref_link').innerText = baseUrl + "/?ref=" + encodeURIComponent(userEmail);
    } else if(data.status === 'pending') {
      setTimeout(checkStatus, 3000);
    } else {
      alert("Account rejected.");
      location.reload();
    }
  }

  function updateUI(balance, refCount) {
    document.getElementById('balance').innerText = balance.toFixed(4);
    document.getElementById('ref_count').innerText = refCount;
  }

  async function tap() {
    const res = await fetch('/api/tap', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email: userEmail})
    });
    const data = await res.json();
    if(data.success) {
      document.getElementById('balance').innerText = data.balance.toFixed(4);
    }
  }

  function copyLink() {
    const link = document.getElementById('ref_link').innerText;
    navigator.clipboard.writeText(link);
    alert("Invite link copied!");
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
    wallet = data.get('wallet')
    referrer = data.get('referrer')
    
    try:
        conn = sqlite3.connect('game.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (email, wallet, referrer) VALUES (?, ?, ?)", (email, wallet, referrer))
        conn.commit()
        
        c.execute("SELECT id FROM users WHERE email=?", (email,))
        uid = c.fetchone()[0]
        conn.close()
        
        text = f"👤 **New Signup (TetherTap)**\n\n📧 Email: {email}\n💳 Wallet: {wallet}\n👥 Ref: {referrer if referrer else 'None'}"
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{uid}"),
                   telebot.types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{uid}"))
        
        bot.send_message(ADMIN_ID, text, reply_markup=markup, parse_mode='Markdown')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/status', methods=['POST'])
def status():
    email = request.json.get('email')
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT status, balance, ref_count FROM users WHERE email=?", (email,))
    user = c.fetchone()
    conn.close()
    
    if user:
        return jsonify({"status": user[0], "balance": user[1], "ref_count": user[2]})
    return jsonify({"status": "not_found"})

@app.route('/api/tap', methods=['POST'])
def tap():
    email = request.json.get('email')
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + 0.0001 WHERE email=?", (email,))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE email=?", (email,))
    new_balance = c.fetchone()[0]
    conn.close()
    return jsonify({"success": True, "balance": new_balance})

def run_bot():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
