"""
Document models.
Database models for document metadata and indexing.
"""


class Document:
    """
    Document metadata model.
    Stores uploaded file information and processing status.

    Fields:
        id: Unique identifier
        title: Human-readable title
        original_filename: Original uploaded filename
        file_path: Path to stored file
        mime_type: File MIME type
        size_bytes: File size in bytes
        source: Document source ('upload', 'link', etc.)
        status: Document state ('uploaded', 'processing', 'indexed', 'failed')
        processing_status: Detailed processing state
        summary_status: Summary generation state
        summary: Generated document summary
        error_message: Error details if processing failed
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    def __init__(self):
        # TODO: Initialize document attributes
        pass

    def set_status(self, status):
        # TODO: Update document status with validation
        pass

    def set_processing_status(self, processing_status):
        # TODO: Update processing status
        pass

    def mark_indexed(self):
        # TODO: Mark document as successfully indexed
        pass

    def mark_failed(self, error_message):
        # TODO: Mark document as failed with error
        pass


class DocumentIndex:
    """
    Document index metadata model.
    Tracks vector indexing status and collection info.

    Fields:
        id: Unique identifier
        document: Reference to Document
        vector_collection: Vector store collection name
        chunk_count: Number of chunks created
        index_status: Indexing state
        last_indexed_at: Timestamp of last indexing
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    def __init__(self):
        # TODO: Initialize document index attributes
        pass

    def update_chunk_count(self, count):
        # TODO: Update chunk count after indexing
        pass
