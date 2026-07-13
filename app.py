from flask import Flask, request, jsonify
from models import db, User, Account
from flask_jwt_extended import JWTManager, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash




app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///securebank.db"

app.config["JWT_SECRET_KEY"] = "youll-never-guess-this"
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

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return("User already exists, please choose a different username")

    hashed_password = generate_password_hash(password)

    new_user = User(username=username, password=hashed_password, email=email)
    db.session.add(new_user)
    db.session.commit()
    return "User registered succesfully", 201



@app.route('/login', methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user_check = User.query.filter_by(username=username).first()
    if user_check is None:
        return "Please try again.", 401

    if check_password_hash(user_check.password, password):
        access_token = create_access_token(identity=user_check.id)
        return jsonify(access_token=access_token), 200
    else:
        return "invalid username or password", 401






if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)


    