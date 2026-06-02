CREATE SCHEMA IF NOT EXISTS faiss_db
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE faiss_db;

CREATE TABLE IF NOT EXISTS `conversation` (
    conversation_id UUID PRIMARY KEY DEFAULT (UUID_v7()),
    conversation_title VARCHAR(32) NOT NULL,
    conversation_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `faiss_index` (
    faiss_index_id UUID PRIMARY KEY DEFAULT (UUID_v7()),
    faiss_index_file_name VARCHAR(128) NOT NULL,
    faiss_index_is_active bool NOT NULL DEFAULT true,
    faiss_index_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `conversation_files` (
    conversation_files_id UUID PRIMARY KEY DEFAULT (UUID_v7()),
    faiss_index_id UUID,
    conversation_files_conversation_id UUID,
    FOREIGN KEY (faiss_index_id) REFERENCES faiss_index(faiss_index_id),
    FOREIGN KEY (conversation_files_conversation_id) REFERENCES conversation(conversation_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `messages` (
    message_id UUID PRIMARY KEY DEFAULT (UUID_v7()),
    message_conversation_id UUID DEFAULT (UUID_v7()),
    message_is_user_send bool NOT NULL, -- true for user, false for assistant
    message_content TEXT NOT NULL,
    message_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_conversation_id) REFERENCES conversation(conversation_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;