from flask import Flask

app = Flask(__name__)

html = """
<!DOCTYPE html>
<html lang="fa">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>تست دکمه</title>
<style>
  body { font-family: sans-serif; text-align: center; margin-top: 50px; background: #222; color: white; }
  button { padding: 15px 30px; font-size: 18px; cursor: pointer; background: #ffaa00; border: none; border-radius: 8px; margin-top: 20px; }
</style>
</head>
<body>

<h2>تست کارکرد دکمه</h2>
<p id="status">منتظر کلیک...</p>
<button onclick="testBtn()">کلیک کن!</button>

<script>
    function testBtn() {
        document.getElementById('status').innerText = "دکمه کار کرد! ✅";
        document.getElementById('status').style.color = "#00ffcc";
    }
</script>

</body>
</html>
"""

@app.route('/')
def index():
    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
