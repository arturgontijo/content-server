import sys
import logging

import grpc
import concurrent.futures as futures

from threading import Thread
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
        # Just for debugging purpose.
        log.debug("CalculatorServicer created")

    # The method that will be exposed to the snet-cli call command.
    # request: incoming data
    # context: object that provides RPC-specific information (timeout, etc).
    def add(self, request, context):
        # To respond we need to create a Result() object (from .proto file)
        result = Result()

        # ASYNC Content Server Logic
        # - Get an UID for this request (datetime based)
        result.uid = service_db.add(content_id="ADD",
                                    service_name="example_async_service",
                                    content_type="text",
                                    func=self.process_request,
                                    args=request)

        # Re-use the same UID to register another entry
        result.uid = service_db.add(uid=result.uid,
                                    content_id="URL",
                                    service_name="example_async_service",
                                    content_type="url",
                                    func=self.process_request,
                                    args=request)

        log.debug("add({},{},{})=Pending".format(result.uid, request.a, request.b))
        return result

    def sub(self, request, context):
        # To respond we need to create a Result() object (from .proto file)
        result = Result()

        # ASYNC Content Server Logic
        # - Get an UID for this request (datetime based)
        result.uid = service_db.add(content_id="SUB",
                                    service_name="example_async_service",
                                    content_type="text",
                                    func=self.process_request,
                                    args=request)

        log.debug("sub({},{},{})=Pending".format(result.uid, request.a, request.b))
        return result

    def mul(self, request, context):
        # To respond we need to create a Result() object (from .proto file)
        result = Result()

        # ASYNC Content Server Logic
        # - Get an UID for this request (datetime based)
        result.uid = service_db.add(content_id="MUL",
                                    service_name="example_async_service",
                                    content_type="text",
                                    func=self.process_request,
                                    args=request)

        log.debug("mul({},{},{})=Pending".format(result.uid, request.a, request.b))
        return result

    def div(self, request, context):
        # To respond we need to create a Result() object (from .proto file)
        result = Result()

        # ASYNC Content Server Logic
        # - Get an UID for this request (datetime based)
        result.uid = service_db.add(content_id="DIV",
                                    service_name="example_async_service",
                                    content_type="text",
                                    func=self.process_request,
                                    args=request)

        log.debug("div({},{},{})=Pending".format(result.uid, request.a, request.b))
        return result

    @staticmethod
    def process_request(request, uid, content_id):
        # Waiting for queue
        item = f"{uid}#{content_id}"
        queue_pos = service_db.queue_get_pos(item)
        while queue_pos != 0:
            queue_pos = service_db.queue_get_pos(item)
            time.sleep(1)
    
        delay = randint(30, 60)
        print("Delay: ", delay)
        time.sleep(delay)
    
        content = ""
        if content_id == "ADD":
            content = "Result: {}".format(request.a + request.b)
        elif content_id == "SUB":
            content = "Result: {}".format(request.a - request.b)
        elif content_id == "MUL":
            content = "Result: {}".format(request.a * request.b)
        elif content_id == "DIV":
            content = "Result: {}".format(request.a / request.b)
        elif content_id == "URL":
            content = "https://singularitynet.io"
        
        # Got the response, update DB with expiration and content
        service_db.update(uid,
                          content_id,
                          queue_pos=-1,
                          expiration=datetime.strptime("05/10/2019 16:30:00", "%m/%d/%Y %H:%M:%S"),
                          content=content)
    
        log.debug("{}({})={} [Ready]".format(content_id.lower(), uid, content))


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


def init_content_server():
    log.info("Creating Content Server Database...")
    global service_db
    service_db = content_server_db(log=log)
    service_db.create(drop=True)

    log.info("Starting Content Server...")
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
