from flask import Flask, request, render_template_string, redirect, url_for, session, flash
import os
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev_secret_key')

# ---------- Config ----------
PREDEFINED_OTP = os.environ.get('PREDEFINED_OTP', '336333')  # treated as PIN
DATA_PATH = os.environ.get('DATA_PATH', '/mnt/data/synthetic_fraud_dataset_balanced.csv')
FALLBACK_AMOUNT_THRESHOLD = float(os.environ.get('FALLBACK_AMOUNT_THRESHOLD', '10000'))

# ---------- CSS ----------
STYLE = """
<style>
body, html {
    margin: 0;
    padding: 0;
    font-family: 'Roboto', sans-serif;
    background: linear-gradient(135deg, #667eea, #764ba2);
    height: 100%;
}
.wrapper { display: flex; flex-direction: column; min-height: 100vh; }
.container {
  background: linear-gradient(135deg, #c7d2fe, #e0e7ff);
  padding: 30px;
  border-radius: 20px;
  box-shadow: 0px 6px 20px rgba(0,0,0,0.15);
  max-width: 400px;
  margin: auto;
}
h1 { font-size: 30px; font-weight: 700; margin-bottom: 30px; color: #333; text-align: center; }
.input-group { margin-bottom: 20px; text-align: left; }
label { display: block; margin-bottom: 5px; font-weight: 700; color: #555; }
input {
    width: 100%; padding: 12px 15px; border-radius: 10px;
    border: 1px solid #ccc; font-size: 16px; outline: none;
    transition: all 0.3s;
}
input:focus { border-color: #667eea; box-shadow: 0 0 10px rgba(102,126,234,0.3); }
button {
    width: 100%; padding: 15px; background: #667eea; color: #fff;
    font-size: 18px; font-weight: bold; border: none; border-radius: 10px;
    cursor: pointer; transition: all 0.3s;
}
button:hover { background: #5a67d8; transform: scale(1.05); }
.result { margin-top: 25px; font-size: 22px; font-weight: bold; color: #222; text-align: center; }
footer {
  color: #0f0317; text-align: center; padding: 20px 0;
  font-size: 18px; font-weight: 600; letter-spacing: 0.5px;
}
</style>
"""

# ---------- HTML PAGES ----------
PAGE_PHONE = STYLE + """
<div class="wrapper"><div class="container">
  <h1>Step 1 — Enter Phone</h1>
  <form method="post" action="{{ url_for('send_otp') }}">
    <div class="input-group">
      <label>Phone number:</label>
      <input name="phone" required placeholder="e.g. +919876543210">
    </div>
    <button type="submit">Next</button>
  </form>
</div></div>
"""

PAGE_OTP = STYLE + """
<div class="wrapper"><div class="container">
  <h1>Step 2 — Enter PIN</h1>
  <form method="post" action="{{ url_for('verify_otp') }}">
    <input type="hidden" name="phone" value="{{ phone }}">
    <div class="input-group">
      <label>PIN:</label>
      <input name="otp" required type="password" placeholder="Enter PIN">
    </div>
    <button type="submit">Verify PIN</button>
  </form>
</div></div>
"""

PAGE_AMOUNT = STYLE + """
<div class="wrapper"><div class="container">
  <h1>Step 3 — Enter Transaction</h1>
  <p style="text-align:center;">Logged in: {{ phone }}</p>
  <form method="post" action="{{ url_for('predict') }}">
    <div class="input-group">
      <label>Amount (numeric):</label>
      <input name="amount" required type="number" step="0.01" min="0">
    </div>
    <button type="submit">Predict Fraud</button>
  </form>
</div></div>
"""

PAGE_RESULT = STYLE + """
<div class="wrapper"><div class="container">
  <h1>Result</h1>
  <p style="text-align:center;">Phone: {{ phone }}</p>
  <p style="text-align:center;">Amount: {{ amount }}</p>
  <div class="result">Prediction: {{ verdict }}</div>
  <footer><a href="{{ url_for('index') }}">Start Over</a></footer>
</div></div>
"""

# ---------- MODEL TRAINING ----------
_model = None
_feature_names = []
_trained = False

def train_model(path=DATA_PATH):
    global _model, _feature_names, _trained
    if not os.path.exists(path):
        return False
    try:
        df = pd.read_csv(path)
        if df.shape[0] < 50:
            return False
        candidates = [c for c in df.columns if c.lower() in ('is_fraud','fraud','class','label','target')]
        target_col = candidates[0] if candidates else df.columns[-1]
        y = df[target_col]
        X = df.drop(columns=[target_col])
        X = pd.get_dummies(X, drop_first=True)
        _feature_names = X.columns.tolist()

        pipe = Pipeline([
            ('impute', SimpleImputer(strategy='median')),
            ('scale', StandardScaler()),
            ('clf', LogisticRegression(max_iter=1000))
        ])
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        pipe.fit(X_train, y_train)
        _model = pipe
        _trained = True
        return True
    except:
        return False

def load_model():
    global _model, _feature_names, _trained
    if _model is not None:
        return _model, _feature_names
    ok = train_model()
    if ok:
        return _model, _feature_names
    return None, []

# ---------- ROUTES ----------
@app.route('/')
def index():
    return render_template_string(PAGE_PHONE)

@app.route('/send_otp', methods=['POST'])
def send_otp():
    phone = request.form.get('phone')
    if not phone:
        flash('Please provide a phone number')
        return redirect(url_for('index'))
    session['phone'] = phone
    return render_template_string(PAGE_OTP, phone=phone)

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    phone = request.form.get('phone') or session.get('phone')
    otp = request.form.get('otp')
    if str(otp).strip() == str(PREDEFINED_OTP):
        session['verified'] = True
        session['phone'] = phone
        return render_template_string(PAGE_AMOUNT, phone=phone)
    else:
        flash('Incorrect PIN. Try again.')
        return render_template_string(PAGE_OTP, phone=phone)

@app.route('/predict', methods=['POST'])
def predict():
    if not session.get('verified'):
        flash('You must verify PIN first.')
        return redirect(url_for('index'))
    phone = session.get('phone')
    amount_raw = request.form.get('amount')
    try:
        amount = float(amount_raw)
    except Exception:
        flash('Invalid amount')
        return render_template_string(PAGE_AMOUNT, phone=phone)

    model, feature_names = load_model()
    verdict = 'Unknown'

    if model is not None:
        try:
            x = pd.DataFrame([{f: 0 for f in feature_names}])
            for amt_name in ('amount','transaction_amount','amt','TransactionAmt','Amount'):
                if amt_name in x.columns:
                    x[amt_name] = amount
                    break
            preds = model.predict_proba(x)
            fraud_prob = float(preds[0][1]) if preds.shape[1] > 1 else float(preds[0][0])
            verdict = 'FRAUD' if fraud_prob >= 0.5 else 'LEGIT'
        except:
            model = None

    if model is None:
        verdict = 'FRAUD' if amount >= FALLBACK_AMOUNT_THRESHOLD else 'LEGIT'

    return render_template_string(PAGE_RESULT, phone=phone, amount=amount, verdict=verdict)

# ---------- ENTRY POINT ----------
if __name__ == '__main__':
    print('Starting app. PIN =', PREDEFINED_OTP)
    load_model()
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=debug)
