from flask import Flask

app = Flask(__name__, instance_relative_config=True)

@app.route('/')
def home():
    return "Welcome to the worlds most secure bank"


if __name__ == "__main__":
    print("Welcome to my app")
    app.run(debug=True)