from firebase.FirebaseModel import *
from firebase.FirebaseClient import client

"""
  1. Predefined struture를 가지고 컨트롤
"""
class FBController:
    def __init__(self):
        self.db = client.get_client()

    def upload_new_document(self, collection: CollectionModel, doc: DocumentModel):
        if collection.ref == None:
            return -1
        else:
            doc_ref = collection.ref.document()
            doc.addr = doc_ref.path
            doc.UUID = doc.addr.split("/")[-1]               
            upload_data = doc.getDict()
            doc_ref.set(upload_data)
            
            if len(doc.sub_collections) != 0:
                for sub_coll in doc.sub_collections:
                    sub_coll = self.upload(sub_coll)

    def update_document(self, addr, document:DocumentModel):
        doc_ref = self.db.document(addr)
        new_data = document.getDict()
        doc_ref.set(new_data)

    # recursive
    def upload(self, collectionData: CollectionModel):
        # .set 함수는 document 주소로 수행됨.
        # 최상단 collection부터 document 수행 후 진행
        if collectionData.PARENT_DOCUMENT == None: # 최상단 collection
            print(collectionData.name)
            collectionData.ref = self.db.collection(collectionData.name)
        else :
            print(collectionData.name)
            collectionData.ref = self.db.collection(
                collectionData.PARENT_DOCUMENT.addr + f"/{collectionData.name}")

        # document 데이터 업로드
        for doc in collectionData.documents:
            # UUID 가 없는 경우
            if doc.UUID == None:
                doc_ref = collectionData.ref.document()
                doc.addr = doc_ref.path
                doc.UUID = doc.addr.split("/")[-1]
            else:
                doc_ref = self.db.document(doc.addr)

            upload_data = doc.getDict()
            doc_ref.set(upload_data)

            # recursive, sub_collecction에 대해서 반복수행, 
            # sub_collection이 존재하지 않으면 종료
            if len(doc.sub_collections) != 0:
                for sub_coll in doc.sub_collections:
                    sub_coll = self.upload(sub_coll)

        return collectionData
    
    # recursive
    # depth = document level (ex, coll1/doc1 - depth 0)
    #                        (ex, coll1/doc1/coll2/doc2 - depth 1)
    def download_collection(self, name, empty = True, max_depth=-1,  current_depth = 0):
        # depth = 0
        #print(name)
        collection = CollectionModel(name)
        collection.PARENT_DOCUMENT = None
        collection.ref = self.db.collection(name)

        if empty:
            for doc in collection.ref.stream():
                new_doc = DocumentModel.make_form(doc.to_dict())
                new_doc.PARENT_COLLECTION = collection
                new_doc.addr = doc.reference.path
                sub_collections = doc.reference.collections()
                for sub_collection in sub_collections:
                    print(sub_collection.id)
                    new_doc.sub_collections.append(
                        self._download_collection_empty(sub_collection.id, new_doc))
                new_doc.addr = None
                collection.documents.append(new_doc)

                break
            return collection
        else:
            # document ID 다운로드
            for doc in collection.ref.stream():
                #print(f"document, docID = {doc.id}")
                new_doc = DocumentModel.from_dict(doc.to_dict())
                new_doc.PARENT_COLLECTION = collection
                new_doc.UUID = doc.id
                new_doc.addr = doc.reference.path

                doc_ref = doc.reference
                sub_collections = doc_ref.collections()

                for sub_collection in sub_collections:
                    #print(f"doc = {doc.id}, sub = {sub_collection.id}")
                    if max_depth == -1:
                        new_doc.sub_collections.append(
                            self._download_collection(sub_collection.id, new_doc,
                                                    max_depth = max_depth,
                                                    current_depth = current_depth + 1))
                    else:   
                        # depth += 1
                        if current_depth + 1 > max_depth:
                            new_doc.sub_collections.append(CollectionModel(sub_collection.id))
                        else:
                            new_doc.sub_collections.append(
                                self._download_collection(sub_collection.id, new_doc,
                                                        max_depth = max_depth,
                                                        current_depth = current_depth + 1))
                
                collection.documents.append(new_doc)
        return collection
    
    # recursive
    def _download_collection_empty(self, name, doc):
        collection = CollectionModel(name)
        collection.PARENT_DOCUMENT = doc
        collection.ref = self.db.collection(f"{doc.addr}/{name}")

        for doc in collection.ref.stream():
            new_doc = DocumentModel.make_form(doc.to_dict())
            new_doc.PARENT_COLLECTION = collection
            new_doc.addr = doc.reference.path
            sub_collections = doc.reference.collections()

            for sub_collection in sub_collections:
                new_doc.sub_collections.append(
                    self._download_collection_empty(sub_collection.id, new_doc))
            new_doc.addr = None
            collection.documents.append(new_doc)

            break
        return collection

    # recursive
    def _download_collection(self, name, doc, current_depth, max_depth):
        #print(current_depth)
        collection = CollectionModel(name)
        collection.PARENT_DOCUMENT = doc
        collection.ref = self.db.collection(f"{doc.addr}/{name}")

        for doc in collection.ref.stream():
            new_doc = DocumentModel.from_dict(doc.to_dict())
            new_doc.PARENT_COLLECTION = collection
            new_doc.UUID = doc.id
            new_doc.addr = doc.reference.path

            doc_ref = doc.reference
            sub_collections = doc_ref.collections()

            for sub_collection in sub_collections:
                #print(f"doc = {doc.id}, sub = {sub_collection.id}")
                if max_depth == -1:
                    new_doc.sub_collections.append(
                        self._download_collection(sub_collection.id, new_doc,
                                                max_depth = max_depth,
                                                current_depth = current_depth + 1,))
                else:   
                    # depth += 1
                    if current_depth + 1 > max_depth:
                        new_doc.sub_collections.append(CollectionModel(sub_collection.id))
                    else:
                        new_doc.sub_collections.append(
                            self._download_collection(sub_collection.id, new_doc,
                                                    max_depth = max_depth,
                                                    current_depth = current_depth + 1))
            
            collection.documents.append(new_doc)
        return collection