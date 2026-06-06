CREATE SCHEMA IF NOT EXISTS faiss_db
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE faiss_db;

-- TABLE FOR SAVE CONVERSATION, THIS TABLE CAN BE SHARDED OR PARTITIONED IF NECESSARY, WHEN DELETE CONVERSATION, ALL MESSAGES SHOULD BE DELETED, USE CASCADE DELETE
CREATE TABLE IF NOT EXISTS `conversation` (
    conversation_id UUID PRIMARY KEY DEFAULT (UUID_v7()),
    conversation_title VARCHAR(32) NOT NULL,
    conversation_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- TABLE FOR SAVE FAISS INDEX, THIS TABLE CAN BE SHARDED OR PARTITIONED IF NECESSARY, WHEN DELETE CONVERSATION, ALL MESSAGES SHOULD BE DELETED, USE CASCADE DELETE
-- RELATIONSHIP: ONE CONVERSATION - ONE INDEX FILE
CREATE TABLE IF NOT EXISTS `faiss_index_file` (
    faiss_index_id UUID PRIMARY KEY DEFAULT (UUID_v7()),
    faiss_index_conversation_id UUID NOT NULL, -- reference to conversation, one conversation can have multiple index file, but one index file only belong to one conversation
    faiss_index_file_name VARCHAR(128) NOT NULL, -- original file name when uploaded, which can be used for display or reference
    faiss_index_file_path VARCHAR(256) NOT NULL, -- path to local storage
    faiss_index_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- timestamp when the index file is created and it will not update 
    FOREIGN KEY (faiss_index_conversation_id) 
    REFERENCES conversation(conversation_id),
    ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- TABLE FOR SAVE MAPPING BETWEEN CONVERSATION AND FILE, FILE HAS BEEN MANAGED BY CLOUD STORAGE
-- ONE FILE HAVE MANY CONVERSATION, IF DONT HAVE ANY CONVERSATION REFERENCE THIS FILE, THIS FILE CAN BE DELETED, USE CASCADE DELETE
CREATE TABLE IF NOT EXISTS `conversation_file` (
    conversation_file_id UUID PRIMARY KEY DEFAULT (UUID_v7()),
    conversation_file_metadata_id UUID NOT NULL, -- reference to file metadata, one file can be referenced by multiple conversation, but one conversation only belong to one file
    conversation_file_conversation_id UUID NOT NULL, -- reference to conversation, one conversation can have multiple file, but one file only belong to one conversation
    FOREIGN KEY (conversation_file_conversation_id) REFERENCES conversation(conversation_id),
    FOREIGN KEY (conversation_file_metadata_id) 
    REFERENCES file_metadata(file_metadata_id)
    ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- TABLE FOR SAVE MAPPING DB AND FILE ON CLOUD STORAGE, THIS TABLE JUST METADATA 
-- IF FILE ON CLOUD STORAGE DELETED, CHECK IF ANY CONVERSATION REFERENCE THIS FILE, IF NOT, WILL MANUALLY DELETE THIS FILE METADATA
CREATE TABLE IF NOT EXISTS `file_metadata` (
    file_metadata_id UUID PRIMARY KEY DEFAULT (UUID_v7()),
    file_metadata_file_cloud_id UUID NOT NULL DEFAULT (UUID_v4()),
    file_metadata_file_name VARCHAR(128) NOT NULL,
    file_metadata_access_url VARCHAR(256) NOT NULL, -- the path used to access the file on cloud storage, which can be a presigned URL or a relative path in the storage bucket
    file_metadata_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- TABLE FOR SAVE MESSAGES ON CONVERSATION, WHEN QUERY CONVERSATION, JOIN THIS TABLE TO GET MESSAGES, THIS TABLE CAN BE VERY LARGE, CONSIDER SHARDING OR PARTITIONING IF NECESSARY,
-- WHEN DELETE CONVERSATION, ALL MESSAGE SHOULD BE DELETED, USE CASCADE DELETE
CREATE TABLE IF NOT EXISTS `message` (
    message_id UUID PRIMARY KEY DEFAULT (UUID_v7()),
    message_conversation_id UUID NOT NULL, -- reference to conversation, one conversation can have multiple messages, but one message only belong to one conversation
    message_is_user_send bool NOT NULL, -- true for user, false for assistant
    message_content TEXT NOT NULL,
    message_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_conversation_id) 
    REFERENCES conversation(conversation_id)
    ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- WHEN DELETE A CONVERSATION_FILE, CHECK IF THE FILE_METADATA IS STILL REFERENCED BY OTHER CONVERSATION_FILE, IF NOT, DELETE THE FILE_METADATA
DELIMITER //

CREATE TRIGGER trg_cleanup_file_metadata_after_delete
AFTER DELETE ON conversation_file
FOR EACH ROW
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM conversation_file cf
        WHERE cf.conversation_file_metadata_id = OLD.conversation_file_metadata_id
        LIMIT 1
    ) THEN
        DELETE FROM file_metadata
        WHERE file_metadata_id = OLD.conversation_file_metadata_id;
    END IF;
END//

DELIMITER ;