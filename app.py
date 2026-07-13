from flask import Flask
from models import db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///securebank.db"

db.init_app(app)

@app.route('/')
def home():
    return "Welcome to the worlds most secure bank"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)