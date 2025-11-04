<?php

/**
 * Migration: Create ADHD Tables
 *
 * Creates database tables for ADHD features:
 * - adhd_user_preferences
 * - cognitive_load_history
 * - attention_state_history
 * - context_snapshots
 */

namespace Leantime\Plugins\Dopemux\Migrations;

use Leantime\Core\Db\Migration;

class CreateADHDPluginTables extends Migration
{
    public function up(): void
    {
        // Create ADHD user preferences table
        $this->db->exec("
            CREATE TABLE IF NOT EXISTS adhd_user_preferences (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                preferences JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_user (user_id),
                INDEX idx_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ");

        // Create cognitive load history table
        $this->db->exec("
            CREATE TABLE IF NOT EXISTS cognitive_load_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                load_value DECIMAL(3,1) NOT NULL,
                context VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_time (user_id, created_at),
                INDEX idx_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ");

        // Create attention state history table
        $this->db->exec("
            CREATE TABLE IF NOT EXISTS attention_state_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                state ENUM('hyperfocus', 'focused', 'scattered', 'background', 'transition') NOT NULL,
                context VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_time (user_id, created_at),
                INDEX idx_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ");

        // Create context snapshots table
        $this->db->exec("
            CREATE TABLE IF NOT EXISTS context_snapshots (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                name VARCHAR(255) NOT NULL,
                snapshot_data JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_time (user_id, created_at),
                INDEX idx_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ");

        // Create break reminder preferences table
        $this->db->exec("
            CREATE TABLE IF NOT EXISTS break_reminder_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                frequency_minutes INT DEFAULT 25,
                enabled BOOLEAN DEFAULT TRUE,
                last_break TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_user (user_id),
                INDEX idx_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ");
    }

    public function down(): void
    {
        // Drop tables in reverse order
        $this->db->exec("DROP TABLE IF EXISTS break_reminder_settings");
        $this->db->exec("DROP TABLE IF EXISTS context_snapshots");
        $this->db->exec("DROP TABLE IF EXISTS attention_state_history");
        $this->db->exec("DROP TABLE IF EXISTS cognitive_load_history");
        $this->db->exec("DROP TABLE IF EXISTS adhd_user_preferences");
    }
}