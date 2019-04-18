from content_server import Database, serve
from datetime import datetime


def main():
    service_db = Database()
    print("Creating Test Database...")
    service_db.create(drop=True)

    service_db.add("0", "S2VT", 1)
    service_db.update("0", queue=0)
    service_db.update("0",
                      queue=-1,
                      expiration=datetime.strptime("04/10/2019 16:30:00", "%m/%d/%Y %H:%M:%S"),
                      signed_url="https://www.google.com")

    service_db.add("1", "S2VT", 1)
    service_db.update("1", queue=0)

    service_db.add("2", "S2VT", 1)

    service_db.add("3", "S2VT", 1)
    service_db.update("3",
                      queue=-1,
                      expiration=datetime.strptime("04/05/2019 16:30:00", "%m/%d/%Y %H:%M:%S"),
                      signed_url="https://www.google.com")

    service_db.add("4", "S2VT", 2)

    service_db.add("5", "S2VT", 3)
    
    serve(service_db)


if __name__ == '__main__':
    main()
