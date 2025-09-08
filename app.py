from flask import Flask, render_template, request, jsonify, session
import joblib, os, base64

app = Flask(__name__)
app.secret_key = "supersecret"   # required for session storage
model = joblib.load('model.pkl')

# Generate a random challenge for WebAuthn
def generate_challenge():
    return os.urandom(32)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = ''
    if request.method == 'POST':
        # Check if fingerprint was verified (from session)
        bio_verified = session.get("biometric_verified", False)

        if not bio_verified:
            result = "❌ Please verify with fingerprint first!"
        else:
            amt = int(request.form['amount'])
            fr = int(request.form['foreign'])

            bio = 1   # verified → pass 1 to model
            pred = model.predict([[bio, amt, fr]])[0]
            if pred == 0:
                result = "✅ Genuine Transaction"
            else:
                result = "⚠️ Fraudulent Transaction"

        # Reset biometric after each transaction
        session["biometric_verified"] = False

    return render_template('index.html', result=result)

@app.route('/get_challenge')
def get_challenge():
    challenge = generate_challenge()
    return jsonify({"challenge": base64.b64encode(challenge).decode('utf-8')})

@app.route('/verify', methods=['POST'])
def verify():
    # In a real app: verify WebAuthn data properly here
    # For demo: fingerprint always succeeds
    session["biometric_verified"] = True
    return jsonify({"status": "ok"})
    
if __name__ == '__main__':
    app.run(debug=True)
