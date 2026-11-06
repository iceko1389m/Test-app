import sqlite3
import random
import string
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        password TEXT,
        balance REAL DEFAULT 0.0
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

html_game = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TitanTap - Step 1</title>
<link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet" />
<style>
  body { font-family: 'Vazirmatn', sans-serif; background: #0b0f19; color: white; text-align: center; margin-top: 50px; }
  .box { max-width: 350px; margin: 0 auto; background: #151b2b; padding: 20px; border-radius: 15px; }
  input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #2a3441; background: #0b0f19; color: white; box-sizing: border-box; font-family: inherit; }
  button { width: 100%; padding: 15px; background: #ffaa00; color: black; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; font-family: inherit; margin-top: 10px; }
  .link { color: #00ffcc; cursor: pointer; margin-top: 15px; display: inline-block; text-decoration: underline; font-size: 14px; }
  .hide { display: none; }
  .tap-btn { width: 150px; height: 150px; border-radius: 50%; background: #ffaa00; margin: 20px auto; font-size: 60px; display: flex; justify-content: center; align-items: center; cursor: pointer; user-select: none; border: 4px solid #fff; transition: 0.1s; }
  .tap-btn:active { transform: scale(0.95); }
  .balance { font-size: 32px; font-weight: bold; color: #ffaa00; margin: 20px 0; }
</style>
</head>
<body>

<div id="auth" class="box">
    <div id="login-form">
        <h2>ورود به بازی</h2>
        <input type="email" id="l_email" placeholder="ایمیل">
        <input type="password" id="l_pass" placeholder="رمز عبور">
        <button onclick="doLogin()">ورود</button>
        <div class="link" onclick="showForm('reg-form')">ثبت‌نام کنید</div>
        <div class="link" style="color:#888;" onclick="showForm('forgot-form')">فراموشی رمز</div>
    </div>
    
    <div id="reg-form" class="hide">
        <h2>ثبت‌نام</h2>
        <input type="email" id="r_email" placeholder="ایمیل">
        <input type="password" id="r_pass" placeholder="رمز عبور">
        <button onclick="doRegister()">ساخت حساب</button>
        <div class="link" onclick="showForm('login-form')">بازگشت به ورود</div>
    </div>

    <div id="forgot-form" class="hide">
        <h2>فراموشی رمز</h2>
        <input type="email" id="f_email" placeholder="ایمیل خود را وارد کنید">
        <button onclick="doForgot()">بازیابی رمز</button>
        <div class="link" onclick="showForm('login-form')">بازگشت به ورود</div>
    </div>
</div>

<div id="game" class="hide">
    <div class="balance"><span id="balance">0.000</span> TTN</div>
    <div class="tap-btn" onclick="doTap()">🛡️</div>
</div>

<script>
    var currentUser = "";

    function showForm(id) {
        document.getElementById('login-form').classList.add('hide');
        document.getElementById('reg-form').classList.add('hide');
        document.getElementById('forgot-form').classList.add('hide');
        document.getElementById(id).classList.remove('hide');
    }

    function api(url, data, success) {
        fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        })
        .then(function(res) { return res.json(); })
        .then(function(res) {
            if(res.success) success(res);
            else alert(res.message);
        })
        .catch(function(err) { alert("خطا در اتصال به سرور"); });
    }

    function doLogin() {
        var email = document.getElementById('l_email').value;
        var pass = document.getElementById('l_pass').value;
        if(!email || !pass) return alert("همه فیلدها را پر کنید");
        
        api('/api/login', {email: email, password: pass}, function(res) {
            currentUser = email;
            startGame(res.balance);
        });
    }

    function doRegister() {
        var email = document.getElementById('r_email').value;
        var pass = document.getElementById('r_pass').value;
        if(!email || !pass) return alert("همه فیلدها را پر کنید");
        
        api('/api/register', {email: email, password: pass}, function(res) {
            currentUser = email;
            startGame(res.balance);
        });
    }

    function doForgot() {
        var email = document.getElementById('f_email').value;
        if(!email) return alert("ایمیل را وارد کنید");
        
        api('/api/forgot', {email: email}, function(res) {
            alert("رمز جدید شما: " + res.new_password + "\\nلطفا با این رمز وارد شوید.");
        });
    }

    function startGame(balance) {
        document.getElementById('auth').classList.add('hide');
        document.getElementById('game').classList.remove('hide');
        document.getElementById('balance').innerText = balance.toFixed(3);
    }

    function doTap() {
        var bal = parseFloat(document.getElementById('balance').innerText);
        var newBal = bal + 0.001;
        document.getElementById('balance').innerText = newBal.toFixed(3);
        
        api('/api/tap', {email: currentUser, amount: 0.001}, function(res){});
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
    
    if get_user(email):
        return jsonify({"success": False, "message": "این ایمیل قبلا ثبت شده است"})
    
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (email, password, balance) VALUES (?, ?, 0.0)", (email, password))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "balance": 0.0})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    user = get_user(email)
    
    if not user or user[1] != password:
        return jsonify({"success": False, "message": "ایمیل یا رمز عبور اشتباه است"})
        
    return jsonify({"success": True, "balance": user[2]})

@app.route('/api/forgot', methods=['POST'])
def forgot():
    email = request.json.get('email')
    user = get_user(email)
    
    if not user:
        return jsonify({"success": False, "message": "کاربری با این ایمیل یافت نشد"})
        
    new_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE email=?", (new_pass, email))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "new_password": new_pass})

@app.route('/api/tap', methods=['POST'])
def tap():
    data = request.json
    email = data.get('email')
    amount = data.get('amount', 0.001)
    
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE email=?", (amount, email))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
