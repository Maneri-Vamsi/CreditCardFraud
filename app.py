from flask import Flask, render_template, request, jsonify


app = Flask(__name__)

# 🔹 Fraud detection model (dummy rule for now)
def predict_fraud(amount: float) -> str:
    return "fraud" if amount > 50000 else "not fraud"

# 🔹 Home page
@app.route("/")
def index():
    return render_template("index.html")

# 🔹 Step 1: Send OTP
@app.route("/send_otp", methods=["POST"])
def send_otp():
    try:
        data = request.json or {}
        phone = data.get("phone")

        if not phone:
            return jsonify({"status": "fail", "message": "Phone number required"}), 400

        client.verify.v2.services(VERIFY_SID).verifications.create(
            to=phone if phone.startswith("+") else f"+91{phone}",
            channel="sms"
        )
        return jsonify({"status": "ok", "message": "OTP sent successfully"})
    except Exception as e:
        return jsonify({"status": "fail", "message": f"Twilio error: {str(e)}"}), 500

# 🔹 Step 2: Verify OTP
@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    try:
        data = request.json or {}
        phone = data.get("phone")
        code = data.get("otp")

        if not phone or not code:
            return jsonify({"status": "fail", "message": "Phone and OTP required"}), 400

        verification_check = client.verify.v2.services(VERIFY_SID).verification_checks.create(
            to=phone if phone.startswith("+") else f"+91{phone}",
            code=code
        )

        if verification_check.status == "approved":
            return jsonify({"status": "ok", "message": "OTP verified"})
        else:
            return jsonify({"status": "fail", "message": "Invalid or expired OTP"}), 400
    except Exception as e:
        return jsonify({"status": "fail", "message": f"Twilio error: {str(e)}"}), 500

# 🔹 Step 3: Fraud detection (only after OTP verified)
@app.route("/check_fraud", methods=["POST"])
def check_fraud():
    try:
        data = request.json or {}
        amount = data.get("amount")

        if amount is None:
            return jsonify({"status": "fail", "message": "Amount required"}), 400

        try:
            amount = float(amount)
        except ValueError:
            return jsonify({"status": "fail", "message": "Invalid amount"}), 400

        result = predict_fraud(amount)
        return jsonify({"status": "ok", "prediction": result})
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
