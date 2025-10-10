from pymongo import MongoClient

try:
    # connect to MongoDB server
    client = MongoClient("mongodb://localhost:27017/")

    # use cybercap instead of test_db
    db = client["cybercap"]

    # collection
    users = db["users"]

    # insert sample data
    users.insert_one({"name": "Asmita", "role": "Admin"})

    # fetch and print
    for user in users.find():
        print(user)

    print("✅ Connected to cybercap database successfully!")

except Exception as e:
    print("❌ Error:", e)
