from flask import Flask, render_template, jsonify, request
import os, base64

app = Flask(__name__)

# Temporary in-memory storage (replace with DB for production)
users = {}

# Serve home page
@app.route('/')
def index():
    return render_template('index.html')

# Generate challenge for registration/login
@app.route('/challenge', methods=['GET'])
def challenge():
    return jsonify({
        'challenge': base64.b64encode(os.urandom(32)).decode('utf-8')
    })

# Save credential after registration
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    users[username] = data['credential']
    return jsonify({'status': 'ok'})

# Authenticate login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    credential = data['credential']

    if username in users and users[username] == credential:
        return jsonify({'status': 'success'})
    return jsonify({'status': 'fail'})

if __name__ == '__main__':
    app.run(debug=True)
