from flask import Flask, jsonify
import requests

app = Flask(__name__)
BASE = "https://api.github.com"


@app.route("/repos/<username>")
def get_repos(username):
    url = f"{BASE}/users/{username}/repos"
    res = requests.get(url)
    return jsonify(res.json())


if __name__ == "__main__":
    app.run(debug=True)
