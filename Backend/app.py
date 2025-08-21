from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def home():
    return "🚀 CyberCAP is running!"

if __name__ == "__main__":
    app.run(debug=True)
