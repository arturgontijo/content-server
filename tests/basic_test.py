from content_server import ContentServer
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)8s] - %(name)s - %(message)s")
log = logging.getLogger("example_async_service")


def main():
    cs = ContentServer(host="localhost", port=7001, admin_pwd="admin", log=log)
    log.info("Creating Test Database...")
    cs.create(drop=True)

    cs.add("0", "Model", "Service_1")
    cs.add("0", "File_1", "Service_2")
    cs.add("0", "File_2", "Service_3")
    cs.add("0", "File_3", "Service_4")
    cs.add("0", "File_4", "Service_5")
    cs.add("0", "File_5", "Service_6")
    cs.add("0", "File_6", "Service_7")
    
    cs.update("0",
              "Model",
              queue_pos=0)
    
    cs.update("0",
              "Model",
              queue_pos=-1,
              expiration="1m",
              content="https://www.google.com")

    cs.remove("0", "File_4")

    cs.add("1", "File", "Service_1")
    cs.update("1",
              "File",
              queue_pos=0)

    cs.add("2", "File", "Service_1")

    cs.add("3", "File", "Service_1")
    cs.update("3",
              "File",
              queue_pos=-1,
              expiration="1d",
              content="https://www.google.com")

    cs.add("4", "File", "Service_1")

    cs.add("5", "File", "Service_1")
    
    cs.serve()


if __name__ == '__main__':
    main()
