from flask import Flask, request, jsonify
from models import db, User, Account, Transaction
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from sqlalchemy import text


load_dotenv()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///securebank.db"

app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")
jwt = JWTManager(app)


db.init_app(app)

@app.route('/')
def home():
    return "Welcome to the worlds most secure bank"


@app.route('/register', methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if not username or not password or not email:
        return jsonify(error="Username, password, and email are all required"), 400

    if len(password) < 8:
        return jsonify(error="Password must be at least 8 characters"), 400
    
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return("User already exists, please choose a different username")

    hashed_password = generate_password_hash(password)

    new_user = User(username=username, password=hashed_password, email=email)
    db.session.add(new_user)
    db.session.commit()

    new_account = Account(user_id=new_user.id, balance=0)
    db.session.add(new_account)
    db.session.commit()
    return "User registered succesfully", 201


@app.route('/login', methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    query = f"SELECT * FROM user WHERE username='{username}' AND password='{password}'"
    result = db.session.execute(text(query))
    user_row = result.fetchone()
    if user_row is None:
        return jsonify(error="Invalid username or password"), 401

    access_token = create_access_token(identity=str(user_row.id))
    return jsonify(access_token=access_token), 200


@app.route('/profile')
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    current_user = User.query.filter_by(id=str(current_user_id)).first()
    if current_user is None:
        return "Please try again.", 401
    else:
        return jsonify(username=current_user.username, email=current_user.email)


@app.route('/profile/balance', methods=["GET"])
@jwt_required()
def balance():
    current_user_id = get_jwt_identity()
    account = Account.query.filter_by(user_id=str(current_user_id)).first()
    if account is None:
        return "Account doesn't exist", 401
    else:
        return jsonify(balance=account.balance / 100)



@app.route('/transfer',methods=["POST"])
@jwt_required()
def transfer():
    data = request.get_json()
    recipient_username = data.get("recipient")

    recipient_user= User.query.filter_by(username=recipient_username).first()
    if recipient_user is None:
        return jsonify(error="Recipient not found"), 404
    
    recipient_account = Account.query.filter_by(user_id=recipient_user.id).with_for_update().first()
    if recipient_account is None:
        return jsonify(error="Recipient account not found"), 404
    
    amount = data.get("amount")
    if amount is None or amount <= 0:
        return jsonify(error="Invalid transfer amount"), 400
    
    amount_pence = int(amount * 100)
    sender_id = get_jwt_identity()

    sender_account = Account.query.filter_by(user_id=str(sender_id)).with_for_update().first()
    if sender_account is None:
        return jsonify(error="Sender account not found"), 404
    
    if sender_account.balance < amount_pence:
        return jsonify(error="Insufficient funds"), 400
    
    sender_account.balance -= amount_pence
    recipient_account.balance += amount_pence
    new_transaction = Transaction(
        sender=sender_account.id,
        receiver=recipient_account.id,
        amount=amount_pence
    )    
    db.session.add(new_transaction)
    db.session.commit()
    return jsonify(message="Transfer successful", new_balance=sender_account.balance / 100), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    debug_mode = os.environ.get("FLASK_DEBUG", "False") == "True"
    # nosemgrep: python.flask.security.audit.app-run-param-config.avoid_app_run_with_bad_host
    app.run(debug=debug_mode, host="0.0.0.0") # nosec B104 - intentional, required for Docker container networking  
    


    