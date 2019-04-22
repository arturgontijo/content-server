import sys
import logging

import grpc
import concurrent.futures as futures

from threading import Thread
import hashlib
from datetime import datetime
import time
from random import randint
from content_server import Database as content_server_db
from content_server import serve as content_server_serve

import service.common

# Importing the generated codes from buildproto.sh
import service.service_spec.example_async_service_pb2_grpc as grpc_bt_grpc
from service.service_spec.example_async_service_pb2 import Result

logging.basicConfig(level=10, format="%(asctime)s - [%(levelname)8s] - %(name)s - %(message)s")
log = logging.getLogger("example_async_service")

# Content Server DB
service_db = None
queue = []

"""
Simple arithmetic service to test the Snet Daemon (gRPC), dApp and/or Snet-CLI.
The user must provide the method (arithmetic operation) and
two numeric inputs: "a" and "b".

e.g:
With dApp:  'method': mul
            'params': {"a": 12.0, "b": 77.0}
Resulting:  response:
                value: 924.0


Full snet-cli cmd:
$ snet client call mul '{"a":12.0, "b":77.0}'

Result:
(Transaction info)
Signing job...

Read call params from cmdline...

Calling service...

    response:
        value: 924.0
"""


# Create a class to be added to the gRPC server
# derived from the protobuf codes.
class CalculatorServicer(grpc_bt_grpc.CalculatorServicer):
    def __init__(self):
        self.a = 0
        self.b = 0
        self.result = 0
        # Just for debugging purpose.
        log.debug("CalculatorServicer created")

    # The method that will be exposed to the snet-cli call command.
    # request: incoming data
    # context: object that provides RPC-specific information (timeout, etc).
    def add(self, request, context):
        # In our case, request is a Numbers() object (from .proto file)
        self.a = request.a
        self.b = request.b

        # To respond we need to create a Result() object (from .proto file)
        self.result = Result()

        # ASYNC Content Server Logic
        # - Get an UID for this request (datetime based)
        self.result.uid = generate_uid()
        delay = randint(30, 120)
        res_th = Thread(target=async_response, daemon=True, args=(self.result.uid, "ADD", delay, self.a, self.b))
        res_th.start()

        log.debug("add({},{},{},{})=Pending".format(self.result.uid, delay, self.a, self.b))
        return self.result

    def sub(self, request, context):
        # In our case, request is a Numbers() object (from .proto file)
        self.a = request.a
        self.b = request.b

        # To respond we need to create a Result() object (from .proto file)
        self.result = Result()

        # ASYNC Content Server Logic
        # - Get an UID for this request (datetime based)
        self.result.uid = generate_uid()
        delay = randint(30, 120)
        res_th = Thread(target=async_response, daemon=True, args=(self.result.uid, "SUB", delay, self.a, self.b))
        res_th.start()

        log.debug("sub({},{},{},{})=Pending".format(self.result.uid, delay, self.a, self.b))
        return self.result

    def mul(self, request, context):
        # In our case, request is a Numbers() object (from .proto file)
        self.a = request.a
        self.b = request.b

        # To respond we need to create a Result() object (from .proto file)
        self.result = Result()

        # ASYNC Content Server Logic
        # - Get an UID for this request (datetime based)
        self.result.uid = generate_uid()
        delay = randint(30, 120)
        res_th = Thread(target=async_response, daemon=True, args=(self.result.uid, "MUL", delay, self.a, self.b))
        res_th.start()

        log.debug("mul({},{},{},{})=Pending".format(self.result.uid, delay, self.a, self.b))
        return self.result

    def div(self, request, context):
        # In our case, request is a Numbers() object (from .proto file)
        self.a = request.a
        self.b = request.b

        # To respond we need to create a Result() object (from .proto file)
        self.result = Result()

        # ASYNC Content Server Logic
        # - Get an UID for this request (datetime based)
        self.result.uid = generate_uid()
        delay = randint(30, 120)
        res_th = Thread(target=async_response, daemon=True, args=(self.result.uid, "DIV", delay, self.a, self.b))
        res_th.start()

        log.debug("div({},{},{},{})=Pending".format(self.result.uid, delay, self.a, self.b))
        return self.result


# The gRPC serve function.
#
# Params:
# max_workers: pool of threads to execute calls asynchronously
# port: gRPC server port
#
# Add all your classes to the server here.
# (from generated .py files by protobuf compiler)
def serve(max_workers=10, port=7777):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    grpc_bt_grpc.add_CalculatorServicer_to_server(CalculatorServicer(), server)
    server.add_insecure_port("[::]:{}".format(port))
    return server


def async_response(uid, content_id, delay, a, b):
    # ASYNC Content Server Logic
    # - Put the request UID#CONTENT_ID in the Queue of Request
    # - Add it to the Content Server DB
    # - Mock a delay to make it "async"
    # - Update the Content Server DB
    item = f"{uid}#{content_id}"
    queue.append(item)
    queue_pos = queue_get_pos(item)
    
    service_db.add(uid=uid,
                   content_id=content_id,
                   service_name="example_async_service",
                   queue_pos=queue_pos,
                   content_type="text")
    
    while queue_pos != 0:
        queue_pos = queue_get_pos(item)
        time.sleep(1)

    result = 0
    if content_id == "ADD":
        result = a + b
    elif content_id == "SUB":
        result = a - b
    elif content_id == "MUL":
        result = a * b
    elif content_id == "DIV":
        result = a / b

    time.sleep(delay)
    service_db.update(uid,
                      content_id,
                      queue_pos=-1,
                      expiration=datetime.strptime("05/10/2019 16:30:00", "%m/%d/%Y %H:%M:%S"),
                      content="Result: {}".format(result))

    queue_rem_pos(item)
    log.debug("add({})={} [Ready]".format(uid, result))


def queue_get_pos(item):
    return queue.index(item)


def queue_update():
    for item in queue:
        [uid, content_id] = item.split("#")
        service_db.update(uid,
                          content_id,
                          queue_pos=queue_get_pos(item))


def queue_rem_pos(item):
    queue.pop(queue.index(item))
    queue_update()


def generate_uid():
    m = hashlib.sha256()
    m.update(str(datetime.now()).encode("utf-8"))
    m = m.digest().hex()
    # Get only the first and the last 10 hex
    return m[:10] + m[-10:]


def init_content_server():
    global service_db
    service_db = content_server_db(log)
    log.info("Creating Content Server Database...")
    service_db.create(drop=True)
    
    # Start serving at localhost:7001 with "admin" as the admin password
    content_server_serve(host="localhost", port=7001, admin_pwd="admin", service_db=service_db)


if __name__ == "__main__":
    """
    Runs the gRPC server to communicate with the Snet Daemon.
    """
    parser = service.common.common_parser(__file__)
    args = parser.parse_args(sys.argv[1:])
    
    # Initiate Content Server (Database and Server)
    content_server_th = Thread(target=init_content_server, daemon=True)
    content_server_th.start()
    
    service.common.main_loop(serve, args)
