from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Create or connect to a database
db = client['linkedin_profiles']

# Create or connect to a collection
collection = db['alumni_profiles']
