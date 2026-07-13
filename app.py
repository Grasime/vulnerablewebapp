from flask import Flask, request
from models import db, User
from werkzeug.security import generate_password_hash




app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///securebank.db"

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


















if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)


    