from content_server import Database, serve
from datetime import datetime


def main():
    service_db = Database()
    print("Creating Test Database...")
    service_db.create(drop=True)

    service_db.add("0", "Model", "Service_1", 1)
    service_db.update("0", "Model", queue=0)
    service_db.update("0",
                      "Model",
                      queue=-1,
                      expiration=datetime.strptime("05/10/2019 16:30:00", "%m/%d/%Y %H:%M:%S"),
                      signed_url="https://www.google.com")
    service_db.add("0", "File_1", "Service_2", 1)
    service_db.add("0", "File_2", "Service_3", 2)
    service_db.add("0", "File_3", "Service_4", 3)
    service_db.add("0", "File_4", "Service_5", 1)
    service_db.add("0", "File_5", "Service_6", 3)
    service_db.add("0", "File_6", "Service_7", 3)
    service_db.remove("0", "File_4")

    service_db.add("1", "File", "Service_1", 1)
    service_db.update("1", "File", queue=0)

    service_db.add("2", "File", "Service_1", 1)

    service_db.add("3", "File", "Service_1", 1)
    service_db.update("3",
                      "File",
                      queue=-1,
                      expiration=datetime.strptime("04/05/2019 16:30:00", "%m/%d/%Y %H:%M:%S"),
                      signed_url="https://www.google.com")

    service_db.add("4", "File", "Service_1", 2)

    service_db.add("5", "File", "Service_1", 3)
    
    serve(service_db)


if __name__ == '__main__':
    main()
