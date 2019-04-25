from content_server import ContentServer
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)8s] - %(name)s - %(message)s")
log = logging.getLogger("example_async_service")


def main():
    cs = ContentServer(host="localhost", port=7001, admin_pwd="admin", log=log)
    log.info("Creating Test Database...")
    cs.create(drop=True)

    uid_0, content_id_0_model = cs.add(uid="0", service_name="Service_1", rpc_method="Model")
    uid_0, content_id_0_file_1 = cs.add(uid="0", service_name="Service_2", rpc_method="File_1")
    uid_0, content_id_0_file_2 = cs.add(uid="0", service_name="Service_3", rpc_method="File_2")
    uid_0, content_id_0_file_3 = cs.add(uid="0", service_name="Service_4", rpc_method="File_3")
    uid_0, content_id_0_file_4 = cs.add(uid="0", service_name="Service_5", rpc_method="File_4")
    uid_0, content_id_0_file_5 = cs.add(uid="0", service_name="Service_6", rpc_method="File_5")
    uid_0, content_id_0_file_6 = cs.add(uid="0", service_name="Service_7", rpc_method="File_6")
    
    # Processing Model
    cs.update(content_id=content_id_0_model, queue_pos=0)
    
    # Model is Ready, set its content and its expiration to 1 minute.
    cs.update(content_id=content_id_0_model,
              queue_pos=-1,
              expiration="1m",
              content="https://www.google.com")

    # Testing remove
    cs.remove(content_id=content_id_0_file_4)

    uid_1, content_id_1_file = cs.add(uid="1", service_name="Service_1", rpc_method="File")
    cs.update(content_id=content_id_1_file, queue_pos=0)

    uid_2, content_id_2_file = cs.add(uid="2", service_name="Service_1", rpc_method="File")

    uid_3, content_id_3_file = cs.add(uid="3", service_name="Service_1", rpc_method="File")
    cs.update(content_id=content_id_3_file,
              queue_pos=-1,
              expiration="1d",
              content="https://www.google.com")

    uid_4, content_id_3_file = cs.add(uid="4", service_name="Service_1", rpc_method="File")

    uid_5, content_id_3_file = cs.add(uid="5", service_name="Service_1", rpc_method="File")
    
    cs.serve()


if __name__ == '__main__':
    main()
