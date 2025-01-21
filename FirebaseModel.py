from dataclasses import dataclass, field, fields
from typing import List, Tuple, Dict
from abc import ABC
from google.cloud import firestore

from firebase.FirebaseClient import client

"""
  Document 생성 시점 
    1. Google form으로 데이터 생성  - 변수가 전부 정의되어 있음.
    2. Firestore에서 데이터 다운로드 - 변수 정의 x, 동적으로 생성
  생성 시 초기화 할 항목
    1. FORM_FIELDS
  특정 Collection에 할당시 UUID, ref, PARENT_COLLECTION 초기화
"""
@dataclass
class DocumentModel(ABC):
    UUID                : str = field(default=None, init = False)
    ref                 : firestore.DocumentReference = field(default=None, init = False)
    FORM_FIELDS         : List[str] = field(default_factory=list, init=False)
    sub_collections     : List["CollectionModel"] = field(default_factory=list, init=False)
    PARENT_COLLECTION   : "CollectionModel" = field(default=None, init =False)

    # documents 에 사전 정의된 document는 FORM_FIELDS가 자동으로 초기화됨. 아닐 경우 초기화 필요
    def __post_init__(self):
        self.FORM_FIELDS = list(f.name for f in fields(self) if f.init)

    # DB에 접근하여 데이터 관리하기 위한 reference 초기화
    def init_reference(self):
        if self.ref == None:
            if self.UUID == None:
                self.ref = self.PARENT_COLLECTION.ref.document()
                self.UUID = self.ref.path.split("/")[-1]
            else:
                self.ref = self.PARENT_COLLECTION.ref.document(self.UUID)
        return self.ref.path
    
    # 하위 컬렉션 추가
    def add_subcollection(self, *collections : Tuple["CollectionModel", ...]):
        for collection in collections:
            # collection PARENT_DOCUMENT 값 업데이트
            collection.set_parent(self)
            self.sub_collections.append(collection)

    # document 내부 값 수정
    def set_value(self, varName, value):
        if varName in self.FORM_FIELDS:
            setattr(self, varName, value)
    
    def set_parent(self, collection: "CollectionModel"):
        self.PARENT_COLLECTION = collection

    # document 내부 값 전부 dictionary 형태로 반환
    def get_data(self):
        dict_return = {}
        for field in self.FORM_FIELDS:
            dict_return[field] = getattr(self, field)
        return dict_return
    
    # document UUID 반환
    def get_id(self):
        if self.UUID == None:
            return None
        else:
            return self.UUID
    
    def contains(self, value):
        for key in self.FORM_FIELDS:
            tmp = getattr(self, key)
            if value == tmp:
                return True
            else:
                return False
    
    @classmethod
    def from_dict(cls, data: Dict):
        instance = cls()
        for key, value in data.items():
            setattr(instance, key, value)
            instance.FORM_FIELDS.append(key)
        
        return instance

    @classmethod
    def make_form(cls, data: Dict):
        instance = cls()
        for key, value in data.items():
            setattr(instance, key, None)
            instance.FORM_FIELDS.append(key)
        return instance
        
@dataclass
class CollectionModel:
    name            : str
    doc_model       : DocumentModel
    ref             : firestore.CollectionReference = field(default=None, init=False)
    documents       : List[DocumentModel] = field(default_factory = list)
    PARENT_DOCUMENT : DocumentModel = field(default=None, init=False)

    def __post_init__(self):
        self.init_reference()

    def init_reference(self):
        if self.PARENT_DOCUMENT == None:
            self.ref = client.db.collection(self.name)
        else:
            self.ref = client.db.collection(f"{self.PARENT_DOCUMENT.ref.path}/{self.name}")

    def add_document(self, *documents: Tuple[DocumentModel, ...]):
        for doc in documents:
            if type(doc) == type(self.doc_model):
                doc.set_parent(self)
                self.documents.append(doc)
            else:
                continue

    def get_document(self, key=None):
        if key != None:
            for doc in self.documents:
                if doc.contains(key):
                    return doc
            return None
        else:
            return self.documents

    def update_documents(self, doc):
        pass

    def delete_document(self):
        pass

    def set_parent(self, document: DocumentModel):
        self.PARENT_DOCUMENT = document