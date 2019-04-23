import os
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
from threading import Thread
import re
import logging

from flask import Flask, render_template, redirect, session, request
from flask_sqlalchemy import SQLAlchemy

__version__ = "0.1.0"

app_folder = Path(__file__).absolute().parent
cwd = os.getcwd()
db_file_folder = "content_db"

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI=f"sqlite:///{cwd}/{db_file_folder}/content.db",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=b"_5#y2L'F4Q8z\n\xec]/")

db = SQLAlchemy(app)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)8s] - %(name)s - %(message)s")
_log = logging.getLogger('werkzeug')
_log.setLevel(logging.ERROR)
app.logger.setLevel(logging.ERROR)


class UID(db.Model):
    __tablename__ = "uid"
    uid = db.Column(db.String(20), primary_key=True, unique=True, nullable=False)
    contents = db.relationship("Content", backref='uid', lazy=True, cascade="all, delete, delete-orphan")
    
    def __repr__(self):
        return "{}".format(self.uid)

    
class Content(db.Model):
    __tablename__ = "content"
    content_id = db.Column(db.String(41), primary_key=True, nullable=False)
    service_name = db.Column(db.String(32), default="")
    queue_pos = db.Column(db.Integer, nullable=False)
    expiration = db.Column(db.DateTime)
    creation = db.Column(db.DateTime, nullable=False, default=datetime.now)
    content_type = db.Column(db.String(10), default="text")
    content = db.Column(db.String(4096), default=None)
    content_uid = db.Column(db.String(20), db.ForeignKey('uid.uid'), nullable=False)
    
    def __repr__(self):
        return "UID: {}\nQueue: {}\nExpiration: {}\nCreation: {}\nContent: {}".format(
            self.content_uid,
            self.queue_pos,
            self.expiration,
            self.creation,
            self.content)


class ContentServer:
    def __init__(self, host="localhost", port=7000, admin_pwd="admin", queue=None, log=None):
        self.host = host
        self.port = port
        self.admin_pwd = admin_pwd
        
        self.queue = []
        if queue:
            self.queue = queue

        self.log = log

    # ============================================ DB Methods ==========================================================
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
    
    def add(self, uid=None, content_id=None, service_name=None, content_type=None, func=None, args=None):
        if not uid:
            uid = self._generate_uid()

        if self.log:
            self.log.info("Adding content: {} {}".format(uid, content_id))
        
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

        if func:
            res_th = Thread(target=func, daemon=True, args=(uid, content_id, ), kwargs=args)
            res_th.start()
        
        return uid
    
    def update(self, uid, content_id, queue_pos, expiration=None, content=None):
        if self.log:
            self.log.info("Updating content: {} {} Queue: {}".format(uid, content_id, queue_pos))
        
        item = f"{uid}#{content_id}"
        entry = self.query_one_uid(uid)
        if entry and entry.contents:
            for _, c in enumerate(entry.contents):
                if c.content_id == item:
                    c.queue_pos = queue_pos
                    if expiration:
                        c.expiration = datetime.now() + self._get_delta_str(expiration)
                    if content:
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
                db.session.commit()
                # If no more contents for this UID(entry), remove it
                if not entry.contents:
                    db.session.delete(entry)
                    db.session.commit()
            else:
                db.session.delete(entry)
                db.session.commit()

    # ==================================================================================================================

    @staticmethod
    def _generate_uid():
        m = hashlib.sha256()
        m.update(str(datetime.now()).encode("utf-8"))
        m = m.digest().hex()
        # Get only the first and the last 10 hex
        return m[:10] + m[-10:]
    
    @staticmethod
    def _get_delta_str(time_str):
        """ Receive and parse a string to timedelta() """
        regex = re.compile(r'((?P<days>\d+?)d)?((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')
        parts = regex.match(time_str)
        if not parts:
            return timedelta()
        parts = parts.groupdict()
        time_params = {}
        for (name, param) in parts.items():
            if param:
                time_params[name] = int(param)
        return timedelta(**time_params)

    # ========================================== Queue Methods =========================================================
    def queue_get_pos(self, item):
        """ Return the position of item in the Queue """
        return self.queue.index(item)

    def queue_update(self):
        """ Update all positions in the Queue """
        for item in self.queue:
            [uid, content_id] = item.split("#")
            self.update(uid,
                        content_id,
                        queue_pos=self.queue_get_pos(item))

    def queue_rem_pos(self, item):
        """ Remove the position of item in the Queue """
        self.queue.pop(self.queue.index(item))
        self.queue_update()

    # ==================================================================================================================

    def serve(self):
        """ Wraps Flask routes and starts its APP """
        
        def get_content_list(uid):
            """ Get and Preprocess data from the DB to be used in the Dashboard """
            content_list = []
            uid = self.query_one_uid(uid)
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
                        position = status = "Expired"
                        btn_type = "danger"
                        btn_disabled = "disabled"
                        content = ""
                        expiration = c.expiration.strftime("%m/%d/%Y, %H:%M:%S")
                    
                    d = {
                        "uid": c.uid,
                        "service": c.service_name,
                        "content_id": c.content_id,
                        "queue_pos": position,
                        "button_class": f"btn btn-block btn-{btn_type} btn-sm {btn_disabled}",
                        "status": status,
                        "content_type": c.content_type,
                        "content": content if content is not None else status,
                        "expiration": expiration,
                        "date": c.creation.strftime("%m/%d/%Y, %H:%M:%S")
                    }
                    content_list.append(d)
            return content_list
        
        def check_uid(uid):
            if self.query_one_uid(uid):
                return True
            return False
        
        # ============================================ FLASK Routes ====================================================
        @app.route("/", methods=["GET", "POST"])
        def root():
            if "logged" in session and session["logged"]:
                return redirect("/dashboard")
            else:
                return render_template("login.html")

        @app.route("/dashboard", methods=["GET", "POST"])
        def dashboard():
            uid = None
            if request.method == "POST":
                uid = request.form.get("uid")
            elif "logged" in session and session["logged"]:
                uid = session["uid"]
                
            admin = False
            if uid == self.admin_pwd:
                admin = True
                content_list = []
                for uid_entry in self.query_all_uid():
                    content_list.extend(get_content_list(uid_entry.uid))
                session["uid"] = uid
                session["logged"] = True
                return render_template("dashboard.html",
                                       admin=admin,
                                       content_list=content_list)
            elif check_uid(uid):
                session["uid"] = uid
                session["logged"] = True
                content_list = get_content_list(session["uid"])
                return render_template("dashboard.html",
                                       admin=admin,
                                       content_list=content_list)
            return redirect("/")
        
        @app.route("/logout")
        def logout():
            session["logged"] = False
            session["uid"] = -1
            return redirect("/")
    
        # POST API - Add new entry in the DB
        @app.route("/post_add", methods=["POST"])
        def post_add():
            try:
                if request.method == "POST":
                    user_pwd = request.form.get("user_pwd", None)
                    if user_pwd == self.admin_pwd:
                        uid = request.form.get("uid", None)
                        content_id = request.form.get("content_id", None)
                        service_name = request.form.get("service_name", None)
                        content_type = request.form.get("content_type", None)
                        uid = self.add(uid=uid,
                                       content_id=content_id,
                                       service_name=service_name,
                                       content_type=content_type)
                        return uid
                    else:
                        return "Denied"
            except Exception as e:
                return str(e)

        # POST API - Update an entry in the DB
        @app.route("/post_update", methods=["POST"])
        def post_update():
            try:
                if request.method == "POST":
                    user_pwd = request.form.get("user_pwd", None)
                    if user_pwd == self.admin_pwd:
                        uid = request.form.get("uid", None)
                        content_id = request.form.get("content_id", None)
                        queue_pos = request.form.get("queue_pos", None)
                        expiration = request.form.get("expiration", None)
                        content = request.form.get("content", None)
                        self.update(uid=uid,
                                    content_id=content_id,
                                    queue_pos=int(queue_pos),
                                    expiration=expiration,
                                    content=content)
                        return uid
                    else:
                        return "Denied"
            except Exception as e:
                return str(e)

        # POST API - Remove an entry from the DB
        @app.route("/post_remove", methods=["GET", "POST"])
        def post_remove():
            try:
                if request.method == "GET":
                    if session["uid"] == self.admin_pwd:
                        uid = request.args.get("uid")
                        content_id = request.args.get("content_id")
                        self.remove(uid, content_id)
                    return redirect("/")
                elif request.method == "POST":
                    user_pwd = request.form.get("user_pwd", None)
                    if user_pwd == self.admin_pwd:
                        uid = request.form.get("uid", None)
                        content_id = request.form.get("content_id", None)
                        self.remove(uid, content_id)
                        return uid
                    else:
                        return "Denied"
            except Exception as e:
                return str(e)

        # POST API - Return the positing of an entry in the Queue
        @app.route("/queue_get_pos", methods=["POST"])
        def queue_get_pos():
            try:
                if request.method == "POST":
                    uid = request.form.get("uid", None)
                    content_id = request.form.get("content_id", None)
                    return str(self.queue_get_pos(f"{uid}#{content_id}"))
            except Exception as e:
                return str(e)

        # ==============================================================================================================

        # Running Flask App...
        app.run(debug=False,
                host=self.host,
                port=self.port,
                use_reloader=False,
                threaded=True,
                passthrough_errors=True)
