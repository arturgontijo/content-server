import os
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, session, request
from flask_sqlalchemy import SQLAlchemy

__version__ = "0.0.1"

app_folder = Path(__file__).absolute().parent
cwd = os.getcwd()
db_file_folder = "content_db"

app = Flask(__name__)
app.config.update(
    TESTING=True,
    SQLALCHEMY_DATABASE_URI=f"sqlite:///{cwd}/{db_file_folder}/content.db",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=b"_5#y2L'F4Q8z\n\xec]/")

db = SQLAlchemy(app)


class UID(db.Model):
    __tablename__ = "uid"
    uid = db.Column(db.String(80), primary_key=True, unique=True, nullable=False)
    contents = db.relationship("Content", backref='uid', lazy=True, cascade="all, delete, delete-orphan")
    
    def __repr__(self):
        return "{}".format(self.uid)

    
class Content(db.Model):
    __tablename__ = "content"
    content_id = db.Column(db.String(80), primary_key=True, nullable=False)
    service_name = db.Column(db.String(200), default="")
    queue = db.Column(db.Integer, nullable=False)
    expiration = db.Column(db.DateTime)
    creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.String(200), default=None)
    content_uid = db.Column(db.Integer, db.ForeignKey('uid.uid'), nullable=False)
    
    def __repr__(self):
        return "<UID {}><Queue {}><Content {}><Expiration {}><Creation {}>".format(
            self.content_uid,
            self.queue,
            self.content,
            self.expiration,
            self.creation)


class Database:
    @staticmethod
    def create(drop=False):
        if not os.path.exists(db_file_folder):
            os.makedirs(db_file_folder)
        elif drop:
            db.drop_all()
        db.create_all()
    
    def add(self, uid, content_id, service_name, queue):
        print("Adding content: ", uid, content_id)
        entry = self.query_one_uid(uid)
        if not entry:
            entry = UID(uid=uid)
        entry.contents.append(Content(content_id=f"{uid}#{content_id}", service_name=service_name, queue=queue))
        db.session.add(entry)
        db.session.commit()
    
    def update(self, uid, content_id, queue, expiration=None, signed_url=None):
        print("Updating content: ", uid, content_id)
        entry = self.query_one_uid(uid)
        if entry and entry.contents:
            for _, c in enumerate(entry.contents):
                if c.content_id == f"{uid}#{content_id}":
                    c.queue = queue
                    c.expiration = expiration
                    c.content = signed_url
            db.session.commit()
    
    def remove(self, uid, content_id=None):
        print("Removing content: ", uid, content_id)
        entry = self.query_one_uid(uid)
        if entry:
            if content_id:
                db.session.delete(self.query_one_content(uid, content_id))
            else:
                db.session.delete(entry)
            db.session.commit()
    
    @staticmethod
    def query_all_uid():
        return UID.query.all()
    
    @staticmethod
    def query_one_uid(uid):
        return UID.query.filter_by(uid=uid).first()

    @staticmethod
    def query_one_content(uid, content_id):
        return Content.query.filter_by(content_id=f"{uid}#{content_id}").first()


def serve(service_db=None):
    if not service_db:
        service_db = Database()
    
    def get_content_list(uid):
        content_list = []
        uid = service_db.query_one_uid(uid)
        if uid and uid.contents:
            for c in uid.contents:
                if c.queue == -1:
                    position = status = "Ready"
                    btn_type = "success"
                elif c.queue == 0:
                    position = status = "Processing"
                    btn_type = "info"
                else:
                    position = c.queue
                    status = "Pending"
                    btn_type = "warning"
                
                btn_disabled = "disabled" if c.uid != uid else ""
                url = "" if c.uid != uid else c.content
                
                expiration = c.expiration.strftime("%m/%d/%Y, %H:%M:%S") if c.expiration else status
                if not c.expiration:
                    btn_disabled = "disabled"
                elif c.expiration <= datetime.now():
                    btn_type = "danger"
                    btn_disabled = "disabled"
                    status = "Expired"
                    url = ""
                    expiration = c.expiration.strftime("%m/%d/%Y, %H:%M:%S"),
                
                d = {
                    "uid": c.uid,
                    "service": c.service_name,
                    "content_id": c.content_id,
                    "queue": position,
                    "button_class": f"btn btn-block btn-{btn_type} btn-sm {btn_disabled}",
                    "status": status,
                    "url": url,
                    "expiration": expiration,
                    "date": c.creation.strftime("%m/%d/%Y, %H:%M:%S")
                }
                content_list.append(d)
        return content_list
    
    def check_uid(uid):
        print("Checking UID...")
        if service_db.query_one_uid(uid):
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
    
    # Running Flask App...
    app.run(debug=False, host="0.0.0.0", port=7001, use_reloader=False, passthrough_errors=True)

