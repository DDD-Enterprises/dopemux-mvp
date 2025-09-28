-- iMessage test database schema and data
-- Based on macOS iMessage chat.db structure for comprehensive testing

-- Core iMessage tables
CREATE TABLE message (
    ROWID INTEGER PRIMARY KEY,
    guid TEXT UNIQUE,
    text TEXT,
    attributedBody BLOB,
    is_from_me INTEGER DEFAULT 0,
    handle_id INTEGER,
    service TEXT DEFAULT 'iMessage',
    date INTEGER,
    date_edited INTEGER,
    associated_message_guid TEXT,
    associated_message_type INTEGER DEFAULT 0,
    cache_has_attachments INTEGER DEFAULT 0,
    balloon_bundle_id TEXT
);

CREATE TABLE chat (
    ROWID INTEGER PRIMARY KEY,
    guid TEXT UNIQUE,
    chat_identifier TEXT,
    display_name TEXT,
    service_name TEXT DEFAULT 'iMessage'
);

CREATE TABLE handle (
    ROWID INTEGER PRIMARY KEY,
    id TEXT,
    service TEXT DEFAULT 'iMessage',
    uncanonicalized_id TEXT
);

CREATE TABLE chat_message_join (
    chat_id INTEGER,
    message_id INTEGER,
    PRIMARY KEY (chat_id, message_id)
);

CREATE TABLE attachment (
    ROWID INTEGER PRIMARY KEY,
    filename TEXT,
    uti TEXT,
    mime_type TEXT,
    transfer_name TEXT,
    total_bytes INTEGER,
    created_date INTEGER,
    start_date INTEGER,
    user_info BLOB
);

CREATE TABLE message_attachment_join (
    message_id INTEGER,
    attachment_id INTEGER,
    PRIMARY KEY (message_id, attachment_id)
);

-- Test handles (contacts)
INSERT INTO handle (ROWID, id, service) VALUES
    (1, '+15551234567', 'iMessage'),
    (2, 'friend@example.com', 'iMessage'),
    (3, '+15559876543', 'SMS');

-- Test chat conversations
INSERT INTO chat (ROWID, guid, chat_identifier) VALUES
    (1, 'iMessage;-;+15551234567', '+15551234567'),
    (2, 'iMessage;-;friend@example.com', 'friend@example.com'),
    (3, 'iMessage;-;group123', 'Group Chat');

-- Test messages covering various scenarios
-- Basic messages (Apple epoch: 2001-01-01 = 0, so adding realistic timestamps)
INSERT INTO message (ROWID, guid, text, is_from_me, handle_id, service, date) VALUES
    (1, 'msg-001', 'Hello there!', 0, 1, 'iMessage', 663360000), -- ~Jan 2022 in Apple epoch seconds
    (2, 'msg-002', 'Hey! How are you?', 1, NULL, 'iMessage', 663360060),
    (3, 'msg-003', 'I''m doing well, thanks for asking', 0, 1, 'iMessage', 663360120),
    (4, 'msg-004', 'Want to grab lunch sometime?', 1, NULL, 'iMessage', 663360180);

-- Reply messages (using associated_message_guid for threading)  
INSERT INTO message (ROWID, guid, text, is_from_me, handle_id, service, date, associated_message_guid, associated_message_type) VALUES
    (5, 'msg-005', 'Sure! How about tomorrow?', 0, 1, 'iMessage', 663360240, 'msg-004', 0),
    (6, 'msg-006', 'Perfect! Let''s meet at noon.', 1, NULL, 'iMessage', 663360300, 'msg-005', 0);

-- Reaction messages (tapbacks) - associated_message_type 2000-2005 for reactions
INSERT INTO message (ROWID, guid, text, is_from_me, handle_id, service, date, associated_message_guid, associated_message_type) VALUES
    (7, 'react-001', '', 0, 1, 'iMessage', 663360360, 'msg-006', 2001), -- like
    (8, 'react-002', '', 1, NULL, 'iMessage', 663360420, 'msg-003', 2000), -- love
    (9, 'react-003', '', 0, 1, 'iMessage', 663360480, 'msg-002', 2003), -- laugh
    (10, 'react-004', '', 1, NULL, 'iMessage', 663360540, 'msg-001', 2004); -- emphasize

-- Messages with different timestamp formats (nanoseconds)
INSERT INTO message (ROWID, guid, text, is_from_me, handle_id, service, date) VALUES
    (11, 'msg-nano-001', 'Testing nanosecond timestamps', 0, 2, 'iMessage', 663360000000000000), -- nanoseconds
    (12, 'msg-micro-001', 'Testing microsecond timestamps', 1, NULL, 'iMessage', 663360060000000); -- microseconds

-- SMS message 
INSERT INTO message (ROWID, guid, text, is_from_me, handle_id, service, date) VALUES
    (13, 'sms-001', 'This is an SMS message', 0, 3, 'SMS', 663360600);

-- Message with attachment
INSERT INTO message (ROWID, guid, text, is_from_me, handle_id, service, date, cache_has_attachments) VALUES
    (14, 'msg-attach-001', 'Check out this photo!', 1, NULL, 'iMessage', 663360660, 1);

-- Test attachments
INSERT INTO attachment (ROWID, filename, uti, mime_type, transfer_name, total_bytes) VALUES
    (1, 'photo.jpg', 'public.jpeg', 'image/jpeg', 'IMG_001.jpeg', 1048576),
    (2, 'video.mp4', 'public.mpeg-4', 'video/mp4', 'MOV_001.mp4', 5242880),
    (3, 'document.pdf', 'com.adobe.pdf', 'application/pdf', 'document.pdf', 524288);

-- Link messages to chats
INSERT INTO chat_message_join (chat_id, message_id) VALUES
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10), -- Phone number chat
    (2, 11), (2, 12), -- Email chat  
    (3, 13), -- SMS chat
    (1, 14); -- Photo message in phone chat

-- Link attachments to messages
INSERT INTO message_attachment_join (message_id, attachment_id) VALUES
    (14, 1); -- Photo attached to message 14

-- Edge cases: orphaned reaction (target message doesn't exist)
INSERT INTO message (ROWID, guid, text, is_from_me, handle_id, service, date, associated_message_guid, associated_message_type) VALUES
    (15, 'react-orphan', '', 0, 1, 'iMessage', 663360720, 'non-existent-msg', 2001);

-- Edge case: message with no handle_id (should default to unknown)
INSERT INTO message (ROWID, guid, text, is_from_me, handle_id, service, date) VALUES
    (16, 'msg-no-handle', 'Message with no handle', 0, NULL, 'iMessage', 663360780);

-- Edge case: message with null/empty text
INSERT INTO message (ROWID, guid, text, is_from_me, handle_id, service, date) VALUES
    (17, 'msg-empty', NULL, 1, NULL, 'iMessage', 663360840),
    (18, 'msg-blank', '', 0, 1, 'iMessage', 663360900);

-- Modern macOS Ventura+ messages with attributedBody encoding (hex blobs)
-- Simulating encoded NSMutableAttributedString - in reality these would be complex binary data
-- For testing, we'll use simplified hex representations
INSERT INTO message (ROWID, guid, text, attributedBody, is_from_me, handle_id, service, date) VALUES
    (19, 'msg-attributed-001', NULL, X'62706c6973743030d40102030405060708090a582476657273696f6e58246f626a65637473592461726368697665725424746f7012000186a0', 0, 1, 'iMessage', 663360960),
    (20, 'msg-attributed-002', NULL, X'62706c6973743030d40102030405060708090a582476657273696f6e58246f626a65637473592461726368697665725424746f7012000186a1', 1, NULL, 'iMessage', 663361020);

-- iOS 16+ messages with message_summary_info (edit history)
-- Create message_summary_info table for iOS 16+ compatibility
CREATE TABLE message_summary_info (
    ROWID INTEGER PRIMARY KEY,
    message_rowid INTEGER,
    content BLOB,
    date_edited INTEGER
);

-- Original message that was later edited (text column will be empty after edit)
INSERT INTO message (ROWID, guid, text, is_from_me, handle_id, service, date, date_edited) VALUES
    (21, 'msg-edited-001', NULL, 1, NULL, 'iMessage', 663361080, 663361140);

-- Insert corresponding edit history in message_summary_info (binary plist format)
-- In reality this would contain complex binary plist with edit history
INSERT INTO message_summary_info (message_rowid, content, date_edited) VALUES
    (21, X'62706c6973743030d40102030405060708090a582476657273696f6e58246f626a65637473592461726368697665725424746f7012000186a2', 663361140);

-- Link remaining messages to chats
INSERT INTO chat_message_join (chat_id, message_id) VALUES
    (1, 15), (1, 16), (1, 17), (1, 18), (1, 19), (1, 20), (1, 21);