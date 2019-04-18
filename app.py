import os
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, session, request
from flask_sqlalchemy import SQLAlchemy


app_folder = Path(__file__).absolute().parent
db_file_folder = "./content_db"

app = Flask(__name__)
app.config.update(
    TESTING=True,
    SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_file_folder}/content.db",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=b"_5#y2L'F4Q8z\n\xec]/")

db = SQLAlchemy(app)


class UID(db.Model):
    uid = db.Column(db.String(80), primary_key=True, unique=True, nullable=False)
    service_name = db.Column(db.String(200), default="")
    queue = db.Column(db.Integer, nullable=False)
    url = db.Column(db.String(200), default=None)
    expiration = db.Column(db.DateTime)
    creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return "<UID {}><Queue {}><SignedURL {}><Expiration {}><Creation {}>".format(
            self.uid,
            self.queue,
            self.url,
            self.expiration,
            self.creation)


class Database:
    
    @staticmethod
    def create(drop=False):
        if not os.path.exists(db_file_folder):
            os.makedirs(db_file_folder)
        if drop:
            db.drop_all()
        db.create_all()
    
    def add(self, uid, service_name, queue):
        print("Adding user: ", uid)
        entry = self.query_one_uid(uid)
        if not entry:
            entry = UID(uid=uid, service_name=service_name, queue=queue)
        db.session.add(entry)
        db.session.commit()
    
    def update(self, uid, queue, expiration=None, signed_url=None):
        print("Updating user: ", uid)
        entry = self.query_one_uid(uid)
        if entry:
            entry.queue = queue
            entry.expiration = expiration
            entry.url = signed_url
            db.session.commit()

    def delete(self, uid):
        if self.query_one_uid(uid):
            entry = UID(uid=uid)
            db.session.delete(entry)
            db.session.commit()
    
    @staticmethod
    def query_all_uid():
        return UID.query.all()
    
    @staticmethod
    def query_one_uid(uid):
        return UID.query.filter_by(uid=uid).first()


my_db = Database()


def get_content_list(uid):
    content_list = []
    content = my_db.query_one_uid(uid)
    if content:
        if content.queue == -1:
            position = status = "Ready"
            btn_type = "success"
        elif content.queue == 0:
            position = status = "Processing"
            btn_type = "info"
        else:
            position = content.queue
            status = "Pending"
            btn_type = "warning"
    
        btn_disabled = "disabled" if content.uid != uid else ""
        url = "" if content.uid != uid else content.url
    
        expiration = content.expiration.strftime("%m/%d/%Y, %H:%M:%S") if content.expiration else status
        if not content.expiration:
            btn_disabled = "disabled"
        elif content.expiration <= datetime.now():
            btn_type = "danger"
            btn_disabled = "disabled"
            status = "Expired"
            url = ""
            expiration = content.expiration.strftime("%m/%d/%Y, %H:%M:%S"),
            
        d = {
            "uid": content.uid,
            "service": content.service_name,
            "queue": position,
            "button_class": f"btn btn-block btn-{btn_type} btn-sm {btn_disabled}",
            "status": status,
            "url": url,
            "expiration": expiration,
            "date": content.creation.strftime("%m/%d/%Y, %H:%M:%S")
        }
        content_list.append(d)
    return content_list


def check_uid(uid):
    print("Checking UID...")
    if my_db.query_one_uid(uid):
        return True
    return False


@app.route("/", methods=["GET", "POST"])
def root():
    if "logged" in session and session["logged"]:
        return render_template("dashboard.html",
                               content_list=get_content_list(session["uid"]))
    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uid = request.form.get("uid")
        if check_uid(uid):
            session["uid"] = uid
            session["logged"] = True
            return render_template("dashboard.html",
                                   content_list=get_content_list(session["uid"]))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session["logged"] = False
    session["uid"] = -1
    return render_template("login.html")


def main():
    try:
        print("Creating Database...")
        my_db.create(drop=True)
        
        my_db.add("0", "S2VT", 1)
        my_db.update("0", queue=0)
        my_db.update("0",
                     queue=-1,
                     expiration=datetime.strptime("04/10/2019 16:30:00", "%m/%d/%Y %H:%M:%S"),
                     signed_url="https://www.google.com")
        
        my_db.add("1", "S2VT", 1)
        my_db.update("1", queue=0)

        my_db.add("2", "S2VT", 1)

        my_db.add("3", "S2VT", 1)
        my_db.update("3",
                     queue=-1,
                     expiration=datetime.strptime("04/05/2019 16:30:00", "%m/%d/%Y %H:%M:%S"),
                     signed_url="https://www.google.com")
        
        my_db.add("4", "S2VT", 2)
        
        my_db.add("5", "S2VT", 3)
        
        app.run(debug=False, host="0.0.0.0", port=7001, use_reloader=False, passthrough_errors=True)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
