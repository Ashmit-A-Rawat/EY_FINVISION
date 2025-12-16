from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os
from dotenv import load_dotenv

load_dotenv()

class MongoDB:
    def __init__(self):
        try:
            mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
            self.client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000
            )
            # Test connection
            self.client.admin.command('ismaster')
            self.db = self.client[os.getenv("DATABASE_NAME", "loan_assistant")]
            print("✅ MongoDB connected successfully")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"⚠️ MongoDB connection failed: {e}")
            print("⚠️ Using in-memory fallback storage")
            self.client = None
            self.db = None
            self._in_memory_storage = {
                "customers": {},
                "offers": {}
            }
    
    def get_collection(self, collection_name):
        """Get collection with fallback to in-memory storage"""
        if self.db is not None:
            return self.db[collection_name]
        else:
            # Return mock collection for in-memory storage
            return InMemoryCollection(self._in_memory_storage, collection_name)
    
    def seed_initial_data(self):
        """Seed 10 dummy customers as per challenge requirements"""
        customers = [
            {
                "customer_id": "CUST001",
                "name": "Rahul Sharma",
                "phone": "9876543210",
                "email": "rahul.sharma@example.com",
                "city": "Mumbai",
                "age": 32,
                "credit_score": 785,
                "preapproved_limit": 500000,
                "salary": 85000,
                "existing_loans": 200000,
                "address": "Flat 201, Sunrise Apartments, Andheri West, Mumbai",
                "kyc_verified": True
            },
            {
                "customer_id": "CUST002",
                "name": "Priya Patel",
                "phone": "9876543211",
                "email": "priya.patel@example.com",
                "city": "Delhi",
                "age": 28,
                "credit_score": 720,
                "preapproved_limit": 300000,
                "salary": 60000,
                "existing_loans": 150000,
                "address": "House No. 45, GK-2, New Delhi",
                "kyc_verified": True
            },
            {
                "customer_id": "CUST003",
                "name": "Amit Kumar",
                "phone": "9876543212",
                "email": "amit.kumar@example.com",
                "city": "Bangalore",
                "age": 35,
                "credit_score": 680,
                "preapproved_limit": 200000,
                "salary": 75000,
                "existing_loans": 300000,
                "address": "No. 123, Koramangala, Bangalore",
                "kyc_verified": False
            },
            {
                "customer_id": "CUST004",
                "name": "Sneha Reddy",
                "phone": "9876543213",
                "email": "sneha.reddy@example.com",
                "city": "Hyderabad",
                "age": 29,
                "credit_score": 810,
                "preapproved_limit": 700000,
                "salary": 95000,
                "existing_loans": 100000,
                "address": "Flat 301, Hitech City, Hyderabad",
                "kyc_verified": True
            },
            {
                "customer_id": "CUST005",
                "name": "Vikram Singh",
                "phone": "9876543214",
                "email": "vikram.singh@example.com",
                "city": "Pune",
                "age": 41,
                "credit_score": 650,
                "preapproved_limit": 150000,
                "salary": 55000,
                "existing_loans": 250000,
                "address": "Row House, Kothrud, Pune",
                "kyc_verified": True
            },
            {
                "customer_id": "CUST006",
                "name": "Anjali Mehta",
                "phone": "9876543215",
                "email": "anjali.mehta@example.com",
                "city": "Chennai",
                "age": 31,
                "credit_score": 750,
                "preapproved_limit": 400000,
                "salary": 80000,
                "existing_loans": 180000,
                "address": "Apartment 5B, T Nagar, Chennai",
                "kyc_verified": True
            },
            {
                "customer_id": "CUST007",
                "name": "Rajesh Gupta",
                "phone": "9876543216",
                "email": "rajesh.gupta@example.com",
                "city": "Kolkata",
                "age": 38,
                "credit_score": 695,
                "preapproved_limit": 250000,
                "salary": 70000,
                "existing_loans": 200000,
                "address": "Salt Lake, Sector V, Kolkata",
                "kyc_verified": True
            },
            {
                "customer_id": "CUST008",
                "name": "Meera Iyer",
                "phone": "9876543217",
                "email": "meera.iyer@example.com",
                "city": "Bangalore",
                "age": 27,
                "credit_score": 730,
                "preapproved_limit": 350000,
                "salary": 75000,
                "existing_loans": 120000,
                "address": "Whitefield, Bangalore",
                "kyc_verified": True
            },
            {
                "customer_id": "CUST009",
                "name": "Karthik Reddy",
                "phone": "9876543218",
                "email": "karthik.reddy@example.com",
                "city": "Mumbai",
                "age": 33,
                "credit_score": 770,
                "preapproved_limit": 600000,
                "salary": 90000,
                "existing_loans": 150000,
                "address": "Powai, Mumbai",
                "kyc_verified": True
            },
            {
                "customer_id": "CUST010",
                "name": "Divya Shah",
                "phone": "9876543219",
                "email": "divya.shah@example.com",
                "city": "Ahmedabad",
                "age": 30,
                "credit_score": 710,
                "preapproved_limit": 320000,
                "salary": 68000,
                "existing_loans": 140000,
                "address": "Satellite, Ahmedabad",
                "kyc_verified": True
            }
        ]
        
        offers = [
            {
                "offer_id": "OFFER001",
                "customer_id": "CUST001",
                "loan_type": "personal",
                "max_amount": 500000,
                "interest_rate": 12.5,
                "tenure_options": [12, 24, 36],
                "processing_fee": 1.5
            },
            {
                "offer_id": "OFFER002",
                "customer_id": "CUST002",
                "loan_type": "personal",
                "max_amount": 300000,
                "interest_rate": 13.5,
                "tenure_options": [12, 24],
                "processing_fee": 2.0
            },
            {
                "offer_id": "OFFER003",
                "customer_id": "CUST004",
                "loan_type": "personal",
                "max_amount": 700000,
                "interest_rate": 11.5,
                "tenure_options": [24, 36, 48],
                "processing_fee": 1.0
            },
            {
                "offer_id": "OFFER004",
                "customer_id": "CUST006",
                "loan_type": "personal",
                "max_amount": 400000,
                "interest_rate": 12.0,
                "tenure_options": [12, 24, 36],
                "processing_fee": 1.8
            }
        ]
        
        customers_col = self.get_collection("customers")
        offers_col = self.get_collection("offers")
        
        try:
            # Clear and insert fresh data
            customers_col.delete_many({})
            offers_col.delete_many({})
            
            customers_col.insert_many(customers)
            offers_col.insert_many(offers)
            
            print(f"✅ Seeded {len(customers)} customers and {len(offers)} offers")
            return True
        except Exception as e:
            print(f"⚠️ Error seeding data: {e}")
            return False


class InMemoryCollection:
    """In-memory collection fallback when MongoDB is unavailable"""
    def __init__(self, storage, collection_name):
        self.storage = storage
        self.collection_name = collection_name
        if collection_name not in self.storage:
            self.storage[collection_name] = {}
    
    def find_one(self, query):
        """Find one document matching query"""
        collection = self.storage.get(self.collection_name, {})
        for key, doc in collection.items():
            match = True
            for field, value in query.items():
                if doc.get(field) != value:
                    match = False
                    break
            if match:
                return doc
        return None
    
    def insert_many(self, documents):
        """Insert multiple documents"""
        collection = self.storage[self.collection_name]
        for doc in documents:
            # Use customer_id or offer_id as key
            key = doc.get("customer_id") or doc.get("offer_id") or str(len(collection))
            collection[key] = doc
        return True
    
    def delete_many(self, query):
        """Delete all documents (for reset)"""
        if not query or query == {}:
            self.storage[self.collection_name] = {}
        return True


# Global database instance
db = MongoDB()