from pymongo import MongoClient
import json
import os

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Create or connect to a database
db = client['linkedin_profiles']

# Create or connect to a collection
collection = db['alumni_profiles']

# Import JSON files into MongoDB
directory = './Objects/'
for filename in os.listdir(directory):
    if filename.endswith('.json'):
        with open(os.path.join(directory, filename)) as file:
            data = json.load(file)
            collection.insert_one(data)

print("Data has been imported to MongoDB")
