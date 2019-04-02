from flask import Flask, render_template, session, redirect, request
from pathlib import Path


app_folder = Path(__file__).absolute().parent

app = Flask(__name__)
app.config.update(
    TESTING=True,
    SECRET_KEY=b"_5#y2L'F4Q8z\n\xec]/")


def check_uid(uid):
    if uid in ["1", "2", "3"]:
        return True
    return False


@app.route("/", methods=["GET", "POST"])
def root():
    if "logged" in session and session["logged"]:
        return render_template("dashboard.html")
    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uid = request.form.get("uid")
        if check_uid(uid):
            session["logged"] = True
            return render_template("dashboard.html")
    return render_template("login.html")


@app.route("/logout")
def logout():
    del session["logged"]
    return render_template("login.html")


def main():
    try:
        app.run(debug=False, host="0.0.0.0", port=7001, use_reloader=False, passthrough_errors=True)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
