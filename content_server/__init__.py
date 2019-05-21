import os
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
from threading import Thread
import re
import logging

from flask import Flask, render_template, redirect, session, request
from flask_sqlalchemy import SQLAlchemy

__version__ = "0.2"

app_folder = Path(__file__).absolute().parent
cwd = os.getcwd()
db_file_folder = "content_db"

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI="sqlite:///{}/{}/content.db".format(
        cwd,
        db_file_folder),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=b"_5#y2L'F4Q8z\n\xec]/")

db = SQLAlchemy(app)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)8s]"
                                               " - %(name)s - %(message)s")
_log = logging.getLogger('werkzeug')
_log.setLevel(logging.ERROR)
app.logger.setLevel(logging.ERROR)


class UID(db.Model):
    __tablename__ = "uid"
    uid = db.Column(db.String(20),
                    primary_key=True,
                    unique=True,
                    nullable=False)
    contents = db.relationship("Content",
                               backref='uid',
                               lazy=True,
                               cascade="all, delete, delete-orphan")
    
    def __repr__(self):
        return "{}".format(self.uid)

    
class Content(db.Model):
    __tablename__ = "content"
    content_id = db.Column(db.Integer, primary_key=True, nullable=False)
    service_name = db.Column(db.String(32), default="")
    rpc_method = db.Column(db.String(32), default="")
    message = db.Column(db.String(32), default="")
    queue_pos = db.Column(db.Integer, nullable=False)
    expiration = db.Column(db.DateTime)
    creation = db.Column(db.DateTime, nullable=False, default=datetime.now)
    content_type = db.Column(db.String(10), default="text")
    content = db.Column(db.String(4096), default=None)
    content_uid = db.Column(db.String(20),
                            db.ForeignKey('uid.uid'),
                            nullable=False)
    
    def __repr__(self):
        return "id: {}\n" \
               "UID: {}\n" \
               "Message: {}\n" \
               "Queue: {}\n" \
               "Expiration: {}\n" \
               "Creation: {}\n" \
               "Content: {}".format(self.id,
                                    self.content_uid,
                                    self.message,
                                    self.queue_pos,
                                    self.expiration,
                                    self.creation,
                                    self.content)


class ContentServer:
    def __init__(self, host="localhost", port=7000,
                 admin_pwd="admin", queues=None, log=None):
        self.host = host
        self.port = port
        self.admin_pwd = admin_pwd
        
        self.queues = dict()
        if queues:
            self.queues = queues

        self.log = log

    # ========================= DB Methods ====================================
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
    def query_all_content(uid):
        return Content.query.filter_by(content_uid=uid).all()
    
    @staticmethod
    def query_one_content(content_id):
        return Content.query.filter_by(content_id=content_id).first()
    
    def add(self, uid=None, service_name="test_service", rpc_method=None,
            message=None, content_type=None, func=None, args=None):
        while not uid:
            uid = self._generate_uid()
            entry = self.query_one_uid(uid)
            if entry:
                uid = None

        if self.log:
            self.log.info("Adding content: {} {}".format(uid, rpc_method))
        
        entry = self.query_one_uid(uid)
        if not entry:
            entry = UID(uid=uid)

        if service_name not in self.queues:
            self.queues[service_name] = []
            
        content = Content(service_name=service_name,
                          rpc_method=rpc_method,
                          message=message,
                          queue_pos=len(self.queues[service_name]),
                          content_type=content_type)

        entry.contents.append(content)
        db.session.add(entry)
        db.session.commit()

        self.queues[service_name].append(content.content_id)

        if func:
            res_th = Thread(target=func,
                            daemon=True,
                            args=(uid, content.content_id, rpc_method, ),
                            kwargs=args)
            res_th.start()
        
        return uid, content.content_id
    
    def update(self, content_id, queue_pos=0,
               message=None, expiration=None, content=None):
        if self.log:
            self.log.info("Updating content: {} Queue: {}".format(content_id,
                                                                  queue_pos))

        c = self.query_one_content(content_id)
        if c:
            c.queue_pos = queue_pos
            # Error
            if queue_pos == -2:
                c.expiration = None
            elif expiration:
                c.expiration = datetime.now() + self._get_delta_str(expiration)

            if message:
                c.message = message
            if content:
                c.content = content
                
            db.session.commit()
            
            if queue_pos == -1 or queue_pos == -2:
                self.queue_rem_pos(content_id)
    
    def remove(self, uid=None, content_id=None):
        if self.log:
            self.log.info("Removing content: {}".format(content_id))

        # Remove the UID with all its contents
        if uid:
            entry = self.query_one_uid(uid)
            db.session.delete(entry)
            db.session.commit()
            for content_id in self.query_all_content(uid):
                self.queue_rem_pos(content_id)
        # Else remove just the target content
        elif content_id:
            content = self.query_one_content(content_id)
            if content:
                db.session.delete(content)
                db.session.commit()
            self.queue_rem_pos(content_id)

    # =========================================================================

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
        regex = re.compile(
            r'((?P<days>\d+?)d)?'
            r'((?P<hours>\d+?)h)?'
            r'((?P<minutes>\d+?)m)?'
            r'((?P<seconds>\d+?)s)?')
        parts = regex.match(time_str)
        if not parts:
            return timedelta()
        parts = parts.groupdict()
        time_params = {}
        for (name, param) in parts.items():
            if param:
                time_params[name] = int(param)
        return timedelta(**time_params)

    # ============================ Queue Methods ==============================
    def queue_get_pos(self, content_id):
        """ Return the position of item in the Queue of a Service """
        for k, v in self.queues.items():
            if content_id in v:
                return self.queues[k].index(content_id)
        return -1

    def queue_update(self):
        """ Update all positions in the Queue """
        for k, v in self.queues.items():
            for content_id in self.queues[k]:
                self.update(content_id,
                            queue_pos=self.queue_get_pos(content_id))

    def queue_rem_pos(self, content_id):
        """ Remove an item from the Queue """
        for k, v in self.queues.items():
            if content_id in v:
                self.queues[k].pop(self.queues[k].index(content_id))
                self.queue_update()

    # =========================================================================

    def serve(self):
        """ Wraps Flask routes and starts its APP """
        def get_content_list(uids):
            """
            Get and Preprocess data from the DB to be used in the Dashboard
            """
            content_list = []
            for _uid in uids:
                uid = self.query_one_uid(_uid)
                if uid and uid.contents:
                    for c in uid.contents:
                        if c.queue_pos == -1:
                            position = status = "Ready"
                            btn_type = "success"
                        elif c.queue_pos == -2:
                            position = status = "Error"
                            btn_type = "danger"
                        elif c.queue_pos == 0:
                            position = status = "Processing"
                            btn_type = "info"
                        else:
                            position = c.queue_pos
                            status = "Pending"
                            btn_type = "warning"
                        
                        btn_disabled = "disabled" if c.uid != uid else ""
                        content = "" if c.uid != uid else c.content
                        
                        expiration = c.expiration.strftime(
                            "%m/%d/%Y, %H:%M:%S") if c.expiration else status
                        if not c.expiration:
                            btn_disabled = "disabled"
                        elif c.expiration <= datetime.now():
                            position = status = "Expired"
                            btn_type = "danger"
                            btn_disabled = "disabled"
                            content = ""
                            expiration = c.expiration.strftime(
                                "%m/%d/%Y, %H:%M:%S")
                        
                        d = {
                            "uid": c.uid,
                            "service": c.service_name,
                            "rpc_method": c.rpc_method,
                            "message": c.message,
                            "content_id": c.content_id,
                            "queue_pos": position,
                            "button_class": "btn btn-block btn-{} btn-sm "
                                            "{}".format(btn_type,
                                                        btn_disabled),
                            "status": status,
                            "content_type": c.content_type,
                            "content": content
                            if content is not None else status,
                            "expiration": expiration,
                            "date": c.creation.strftime("%m/%d/%Y, %H:%M:%S")
                        }
                        content_list.append(d)
            return content_list
        
        def check_uid(uid):
            if self.query_one_uid(uid):
                return True
            return False
        
        # ====================== FLASK Routes =================================
        @app.route("/", methods=["GET", "POST"])
        def root():
            if "logged" in session and session["logged"]:
                return redirect("/dashboard")
            else:
                return render_template("login.html")

        @app.route("/dashboard", methods=["GET", "POST"])
        def dashboard():
            uid = request.args.get("uid", None)
            if request.method == "POST":
                uid = request.form.get("uid")
            elif "logged" in session and session["logged"]:
                uid = session["uids"][0]
            
            if "uids" not in session:
                session["uids"] = []

            if uid not in session["uids"]:
                session["uids"].append(uid)
            session["logged"] = True
            
            admin = False
            if uid == self.admin_pwd:
                admin = True
                content_list = []
                for uid_entry in self.query_all_uid():
                    content_list.extend(get_content_list([uid_entry.uid]))
                return render_template("dashboard.html",
                                       user="Admin",
                                       admin=admin,
                                       content_list=content_list)
            elif check_uid(uid):
                return render_template("dashboard.html",
                                       user=session["uids"][0],
                                       admin=admin,
                                       content_list=get_content_list(
                                           session["uids"]))
            session["uids"] = []
            session["logged"] = False
            return redirect("/")
        
        @app.route("/add_uid", methods=["POST"])
        def add_uid():
            if request.method == "POST":
                if "logged" in session and session["logged"]:
                    uid = request.form.get("uid")
                    if check_uid(uid):
                        if uid not in session["uids"]:
                            session["uids"].append(uid)
                            session.modified = True
                    return redirect("/dashboard")
                else:
                    return render_template("login.html")
        
        @app.route("/logout")
        def logout():
            session["uids"] = []
            session["logged"] = False
            return redirect("/")
    
        # POST API - Add new entry in the DB
        @app.route("/post_add", methods=["POST"])
        def post_add():
            try:
                if request.method == "POST":
                    user_pwd = request.form.get("user_pwd", None)
                    if user_pwd == self.admin_pwd:
                        uid = request.form.get("uid", None)
                        service_name = request.form.get("service_name", None)
                        rpc_method = request.form.get("rpc_method", None)
                        content_type = request.form.get("content_type", None)
                        uid, content_id = self.add(uid=uid,
                                                   service_name=service_name,
                                                   rpc_method=rpc_method,
                                                   content_type=content_type)
                        return "{}&{}".format(uid,
                                                  content_id)
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
                        content_id = request.form.get("content_id", None)
                        queue_pos = request.form.get("queue_pos", None)
                        expiration = request.form.get("expiration", None)
                        content = request.form.get("content", None)
                        self.update(content_id=int(content_id),
                                    queue_pos=int(queue_pos),
                                    expiration=expiration,
                                    content=content)
                        return content_id
                    else:
                        return "Denied"
            except Exception as e:
                return str(e)

        # POST API - Remove an entry from the DB
        @app.route("/post_remove", methods=["GET", "POST"])
        def post_remove():
            try:
                if request.method == "GET":
                    if session["uids"][0] == self.admin_pwd:
                        uid = request.args.get("uid", None)
                        content_id = request.args.get("content_id", None)
                        self.remove(uid=uid,
                                    content_id=int(content_id))
                    return redirect("/")
                elif request.method == "POST":
                    user_pwd = request.form.get("user_pwd", None)
                    if user_pwd == self.admin_pwd:
                        uid = request.form.get("uid", None)
                        content_id = request.form.get("content_id", None)
                        self.remove(uid=uid,
                                    content_id=int(content_id))
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
                    content_id = request.form.get("content_id", None)
                    return str(self.queue_get_pos(int(content_id)))
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
