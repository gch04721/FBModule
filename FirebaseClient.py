from google.cloud import firestore
import os

class FBClient:
    _instance = None
    _client = None
    _db = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FBClient, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def initialize(self, key_file: str):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_file
        self._client = firestore.Client()
        
    @property
    def db(self):
        return self._client
    
client = FBClient()