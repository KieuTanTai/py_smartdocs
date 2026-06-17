from abc import ABC, abstractmethod

class IDocumentApplication(ABC):
    @abstractmethod
    def upload_document(self, document_data):
        pass

    @abstractmethod
    def get_document(self, document_id):
        pass

    @abstractmethod
    def update_document(self, document_id, document_data):
        pass

    @abstractmethod
    def delete_document(self, document_id):
        pass