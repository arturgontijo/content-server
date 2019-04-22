import os
from pathlib import Path
from datetime import datetime
import hashlib
from threading import Thread

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
    queue_pos = db.Column(db.Integer, nullable=False)
    expiration = db.Column(db.DateTime)
    creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content_type = db.Column(db.String(20), default="text")
    content = db.Column(db.String(200), default=None)
    content_uid = db.Column(db.Integer, db.ForeignKey('uid.uid'), nullable=False)
    
    def __repr__(self):
        return "<UID {}><Queue {}><Content {}><Expiration {}><Creation {}>".format(
            self.content_uid,
            self.queue_pos,
            self.content,
            self.expiration,
            self.creation)


class Database:
    def __init__(self, queue=None, log=None):
        self.queue = []
        if queue:
            self.queue = queue
        self.log = log

    @staticmethod
    def create(drop=False):
        if not os.path.exists(db_file_folder):
            os.makedirs(db_file_folder)
        elif drop:
            db.drop_all()
        db.create_all()

    @staticmethod
    def query_all_uid():
        return UID.query.all()

    @staticmethod
    def query_one_uid(uid):
        return UID.query.filter_by(uid=uid).first()

    @staticmethod
    def query_one_content(uid, content_id):
        return Content.query.filter_by(content_id=f"{uid}#{content_id}").first()

    @staticmethod
    def _generate_uid():
        m = hashlib.sha256()
        m.update(str(datetime.now()).encode("utf-8"))
        m = m.digest().hex()
        # Get only the first and the last 10 hex
        return m[:10] + m[-10:]
    
    # ------------------------------------------ Queue Methods ---------------------------------------------------------
    def queue_get_pos(self, item):
        return self.queue.index(item)

    def queue_update(self):
        for item in self.queue:
            [uid, content_id] = item.split("#")
            self.update(uid,
                        content_id,
                        queue_pos=self.queue_get_pos(item))

    def queue_rem_pos(self, item):
        self.queue.pop(self.queue.index(item))
        self.queue_update()
    # ------------------------------------------------------------------------------------------------------------------
    
    def add(self, uid=None, content_id=None, service_name=None, content_type=None, func=None, args=None):
        if self.log:
            self.log.info("Adding content: {} {}".format(uid, content_id))
        
        if not uid:
            uid = self._generate_uid()
        
        entry = self.query_one_uid(uid)
        if not entry:
            entry = UID(uid=uid)

        item = f"{uid}#{content_id}"
        self.queue.append(item)
        queue_pos = self.queue_get_pos(item)
        
        entry.contents.append(Content(content_id=f"{uid}#{content_id}",
                                      service_name=service_name,
                                      queue_pos=queue_pos,
                                      content_type=content_type))
        db.session.add(entry)
        db.session.commit()

        res_th = Thread(target=func, daemon=True, args=(args, uid, content_id, ))
        res_th.start()
        
        return uid

    def add_admin(self, uid):
        if self.log:
            self.log.info("Adding Admin: {}".format(uid))
    
        entry = self.query_one_uid(uid)
        if not entry:
            entry = UID(uid=uid)

        db.session.add(entry)
        db.session.commit()
    
    def update(self, uid, content_id, queue_pos, expiration=None, content=None):
        if self.log:
            self.log.info("Updating content: {} {}".format(uid, content_id))
        
        item = f"{uid}#{content_id}"
        entry = self.query_one_uid(uid)
        if entry and entry.contents:
            for _, c in enumerate(entry.contents):
                if c.content_id == item:
                    c.queue_pos = queue_pos
                    c.expiration = expiration
                    c.content = content
            db.session.commit()
            if queue_pos == -1:
                self.queue_rem_pos(item)
    
    def remove(self, uid, content_id=None):
        if self.log:
            self.log.info("Removing content: {} {}".format(uid, content_id))

        entry = self.query_one_uid(uid)
        if entry:
            if content_id:
                db.session.delete(self.query_one_content(uid, content_id))
            else:
                db.session.delete(entry)
            db.session.commit()


def serve(host="0.0.0.0", port=7000, admin_pwd=None, service_db=None, log=None):
    if not service_db:
        service_db = Database(log)
    
    def get_content_list(uid):
        content_list = []
        uid = service_db.query_one_uid(uid)
        if uid and uid.contents:
            for c in uid.contents:
                if c.queue_pos == -1:
                    position = status = "Ready"
                    btn_type = "success"
                elif c.queue_pos == 0:
                    position = status = "Processing"
                    btn_type = "info"
                else:
                    position = c.queue_pos
                    status = "Pending"
                    btn_type = "warning"
                
                btn_disabled = "disabled" if c.uid != uid else ""
                content = "" if c.uid != uid else c.content
                
                expiration = c.expiration.strftime("%m/%d/%Y, %H:%M:%S") if c.expiration else status
                if not c.expiration:
                    btn_disabled = "disabled"
                elif c.expiration <= datetime.now():
                    btn_type = "danger"
                    btn_disabled = "disabled"
                    status = "Expired"
                    content = ""
                    expiration = c.expiration.strftime("%m/%d/%Y, %H:%M:%S"),
                
                d = {
                    "uid": c.uid,
                    "service": c.service_name,
                    "content_id": c.content_id,
                    "queue_pos": position,
                    "button_class": f"btn btn-block btn-{btn_type} btn-sm {btn_disabled}",
                    "status": status,
                    "content_type": c.content_type,
                    "content": content,
                    "expiration": expiration,
                    "date": c.creation.strftime("%m/%d/%Y, %H:%M:%S")
                }
                content_list.append(d)
        return content_list
    
    def check_uid(uid):
        if service_db.query_one_uid(uid):
            return True
        return False
    
    @app.route("/", methods=["GET", "POST"])
    def root():
        if "logged" in session and session["logged"]:
            if admin_pwd and session["uid"] == admin_pwd:
                content_list = []
                for uid_entry in service_db.query_all_uid():
                    content_list.extend(get_content_list(uid_entry.uid))
            else:
                content_list = get_content_list(session["uid"])
            return render_template("dashboard.html",
                                   content_list=content_list)
        return render_template("login.html")
    
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            uid = request.form.get("uid")
            if admin_pwd and uid == admin_pwd:
                content_list = []
                for uid_entry in service_db.query_all_uid():
                    content_list.extend(get_content_list(uid_entry.uid))
                session["uid"] = uid
                session["logged"] = True
                return render_template("dashboard.html",
                                       content_list=content_list)
            elif check_uid(uid):
                session["uid"] = uid
                session["logged"] = True
                content_list = get_content_list(session["uid"])
                return render_template("dashboard.html",
                                       content_list=content_list)
        return render_template("login.html")
    
    @app.route("/logout")
    def logout():
        session["logged"] = False
        session["uid"] = -1
        return render_template("login.html")
    
    # Running Flask App...
    app.run(debug=False, host=host, port=port, use_reloader=False, passthrough_errors=True)

