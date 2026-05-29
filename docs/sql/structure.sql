CREATE SCHEMA IF NOT EXISTS faiss_db;
USE faiss_db;

CREATE TABLE IF NOT EXISTS `conversation` (
    conversation_id BINARY(16) PRIMARY KEY,
    conversation_title VARCHAR(32) NOT NULL,
    conversation_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `faiss_index` (
    faiss_index_id BINARY(16) PRIMARY KEY,
    faiss_index_file_name VARCHAR(128) NOT NULL,
    faiss_index_is_active bool NOT NULL DEFAULT true,
    faiss_index_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `conversation_files` (
    conversation_files_id BINARY(16) PRIMARY KEY,
    conversation_files_conversation_id BINARY(16),
    FOREIGN KEY (conversation_files_conversation_id) REFERENCES conversation(conversation_id)
);

CREATE TABLE IF NOT EXISTS `messages` (
    message_id BINARY(16) PRIMARY KEY,
    message_conversation_id BINARY(16),
    message_is_user_send bool NOT NULL, -- true for user, false for assistant
    message_content TEXT NOT NULL,
    message_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_conversation_id) REFERENCES conversation(conversation_id)
);