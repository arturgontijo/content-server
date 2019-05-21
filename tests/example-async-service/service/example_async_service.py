import sys
import logging

import grpc
import concurrent.futures as futures

from threading import Thread
import time
from random import randint
import requests

from content_server import ContentServer

import service.common

# Importing the generated codes from buildproto.sh
import service.service_spec.example_async_service_pb2_grpc as grpc_bt_grpc
from service.service_spec.example_async_service_pb2 import Result

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)8s]"
                                               " - %(name)s - %(message)s")
log = logging.getLogger("example_async_service")

# Content Server
cs = None
admin_pwd = "admin"
cs_host = "localhost"
cs_port = 7001

"""
Simple arithmetic service to test the SNET Daemon (gRPC), dApp and/or SNET-CLI.
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
        log.info("CalculatorServicer created")

    # The method that will be exposed to the snet-cli call command.
    # request: incoming data
    # context: object that provides RPC-specific information (timeout, etc).
    def add(self, request, context):
        # To respond we need to create a Result() object (from .proto file)
        result = Result()

        # ASYNC Content Server Logic
        # - Get an UID for this request (datetime based)
        result.uid, _ = cs.add(uid=request.uid,
                               service_name="example_async_service",
                               rpc_method="add",
                               content_type="text",
                               func=self.process_request,
                               args={"request": request})

        # Re-use the same UID to register another entry.
        result.uid, _ = cs.add(uid=result.uid,
                               service_name="example_async_service",
                               rpc_method="add_url",
                               content_type="url",
                               func=self.process_request,
                               args={"request": request})

        log.info("add({},{},{})=Pending".format(result.uid,
                                                request.a,
                                                request.b))
        return result

    def sub(self, request, context):
        # To respond we need to create a Result() object (from .proto file)
        result = Result()

        # ASYNC Content Server Logic
        # - Get an UID for this request (datetime based)
        result.uid, _ = cs.add(uid=request.uid,
                               service_name="example_async_service",
                               rpc_method="sub",
                               content_type="text",
                               func=self.process_request,
                               args={"request": request})

        # Re-use the same UID to register another entry (via HTTP POST).
        rpc_method = "post_sub_url"
        r = requests.post("http://{}:{}/post_add".format(cs_host, cs_port),
                          data={
                              "user_pwd": admin_pwd,
                              "uid": result.uid,
                              "service_name": "example_async_service",
                              "rpc_method": rpc_method,
                              "content_type": "url"
                          })
        [_, content_id] = r.text.split("&")

        # Initiate the thread that will handle the request
        sub_post_th = Thread(target=self.process_request_post,
                             daemon=True,
                             args=(content_id, rpc_method, request))
        sub_post_th.start()

        log.info("sub({},{},{})=Pending {}".format(result.uid,
                                                   request.a,
                                                   request.b,
                                                   r.status_code))
        return result

    def mul(self, request, context):
        # To respond we need to create a Result() object (from .proto file)
        result = Result()

        # ASYNC Content Server Logic
        # - Get an UID for this request (datetime based)
        result.uid, _ = cs.add(uid=request.uid,
                               service_name="example_async_service",
                               rpc_method="mul",
                               content_type="text",
                               func=self.process_request,
                               args={"request": request})

        log.info("mul({},{},{})=Pending".format(result.uid, request.a, request.b))
        return result

    def div(self, request, context):
        # To respond we need to create a Result() object (from .proto file)
        result = Result()

        # ASYNC Content Server Logic
        # - Get an UID for this request (datetime based)
        result.uid, _ = cs.add(uid=request.uid,
                               service_name="example_async_service",
                               rpc_method="div",
                               content_type="text",
                               func=self.process_request,
                               args={"request": request})

        log.info("div({},{},{})=Pending".format(result.uid, request.a, request.b))
        return result

    @staticmethod
    def process_request(content_id, rpc_method, **kwargs):
        # Waiting for queue
        queue_pos = cs.queue_get_pos(content_id)
        while queue_pos != 0:
            queue_pos = cs.queue_get_pos(content_id)
            time.sleep(1)
    
        delay = randint(10, 30)
        log.info("Fake Processing Delay: {}".format(delay))
        time.sleep(delay)

        request = None
        for k, v in kwargs.items():
            if k == "request":
                request = v

        content = ""
        if request:
            if rpc_method == "add":
                content = "Result: {}".format(request.a + request.b)
            elif rpc_method == "sub":
                content = "Result: {}".format(request.a - request.b)
            elif rpc_method == "mul":
                content = "Result: {}".format(request.a * request.b)
            elif rpc_method == "div":
                content = "Result: {}".format(request.a / request.b)
            elif "url" in rpc_method:
                content = "https://singularitynet.io"
    
        # Got the response, update DB with expiration and content
        cs.update(content_id,
                  queue_pos=-1,
                  expiration="1d12h",
                  content=content)
    
        log.info("{}({})={} [Ready]".format(rpc_method, content_id, content))

    @staticmethod
    def process_request_post(content_id, rpc_method, request):
        # Waiting for queue
        r = requests.post("http://{}:{}/queue_get_pos".format(cs_host,
                                                               cs_port),
                          data={"content_id": content_id})
        queue_pos = int(r.text)
        while queue_pos != 0:
            r = requests.post("http://{}:{}/queue_get_pos".format(cs_host,
                                                                   cs_port),
                              data={"content_id": content_id})
            queue_pos = int(r.text)
            time.sleep(1)
    
        delay = randint(10, 30)
        log.info("Fake Processing Delay: {}".format(delay))
        time.sleep(delay)
    
        content = ""
        if rpc_method == "add":
            content = "Result: {}".format(request.a + request.b)
        elif rpc_method == "sub":
            content = "Result: {}".format(request.a - request.b)
        elif rpc_method == "mul":
            content = "Result: {}".format(request.a * request.b)
        elif rpc_method == "div":
            content = "Result: {}".format(request.a / request.b)
        elif "url" in rpc_method:
            content = "https://singularitynet.io"
        
        # Got the response, update DB with expiration and content
        r = requests.post("http://{}:{}/post_update".format(cs_host, cs_port),
                          data={
                              "user_pwd": admin_pwd,
                              "content_id": content_id,
                              "queue_pos": -1,
                              "expiration": "2m",
                              "content": content
                          })
    
        log.info("{}({})={} [Ready {}]".format(rpc_method,
                                               content_id,
                                               content,
                                               r.status_code))


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
    global cs
    cs = ContentServer(host=cs_host,
                       port=cs_port,
                       admin_pwd=admin_pwd,
                       log=log)
    
    log.info("Creating Content Server Database...")
    cs.create(drop=True)

    # Start serving at 0.0.0.0:7001 with "admin" as the admin password
    log.info("Starting Content Server...")
    cs.serve()


if __name__ == "__main__":
    """
    Runs the gRPC server to communicate with the SNET Daemon.
    """
    parser = service.common.common_parser(__file__)
    args = parser.parse_args(sys.argv[1:])
    
    # Initiate Content Server (Database and Server)
    content_server_th = Thread(target=init_content_server, daemon=True)
    content_server_th.start()
    
    service.common.main_loop(serve, args)
