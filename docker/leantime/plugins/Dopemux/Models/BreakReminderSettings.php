<?php

/**
 * Break Reminder Settings Model
 *
 * Manages break reminder preferences for users.
 */

namespace Leantime\Plugins\Dopemux\Models;

use Leantime\Core\Db\Base as DbModel;

class BreakReminderSettings extends DbModel
{
    /**
     * Get user's break reminder settings
     */
    public function getUserSettings($userId): array
    {
        $sql = "SELECT frequency_minutes, enabled, last_break, created_at, updated_at
                FROM break_reminder_settings
                WHERE user_id = :user_id";

        $stmt = $this->prepare($sql);
        $stmt->bindParam(':user_id', $userId, PDO::PARAM_INT);
        $stmt->execute();

        $settings = $stmt->fetch(PDO::FETCH_ASSOC);

        return $settings ?: $this->getDefaultSettings();
    }

    /**
     * Update user's break reminder settings
     */
    public function updateUserSettings($userId, $frequency, $enabled): bool
    {
        $sql = "INSERT INTO break_reminder_settings (user_id, frequency_minutes, enabled)
                VALUES (:user_id, :frequency, :enabled)
                ON DUPLICATE KEY UPDATE
                frequency_minutes = VALUES(frequency_minutes),
                enabled = VALUES(enabled)";

        $stmt = $this->prepare($sql);
        $stmt->bindParam(':user_id', $userId, PDO::PARAM_INT);
        $stmt->bindParam(':frequency', $frequency, PDO::PARAM_INT);
        $stmt->bindParam(':enabled', $enabled, PDO::PARAM_BOOL);

        return $stmt->execute();
    }

    /**
     * Update last break timestamp
     */
    public function updateLastBreak($userId): bool
    {
        $sql = "INSERT INTO break_reminder_settings (user_id, last_break)
                VALUES (:user_id, NOW())
                ON DUPLICATE KEY UPDATE last_break = NOW()";

        $stmt = $this->prepare($sql);
        $stmt->bindParam(':user_id', $userId, PDO::PARAM_INT);

        return $stmt->execute();
    }

    /**
     * Check if break is due for user
     */
    public function isBreakDue($userId): bool
    {
        $settings = $this->getUserSettings($userId);

        if (!$settings['enabled']) {
            return false;
        }

        if (!$settings['last_break']) {
            return true; // No break taken yet, assume due
        }

        $lastBreak = strtotime($settings['last_break']);
        $frequencySeconds = $settings['frequency_minutes'] * 60;
        $nextBreakDue = $lastBreak + $frequencySeconds;

        return time() >= $nextBreakDue;
    }

    /**
     * Get default break reminder settings
     */
    private function getDefaultSettings(): array
    {
        return [
            'frequency_minutes' => 25,
            'enabled' => true,
            'last_break' => null,
            'created_at' => date('Y-m-d H:i:s'),
            'updated_at' => date('Y-m-d H:i:s')
        ];
    }

    /**
     * Get break statistics for user
     */
    public function getBreakStats($userId, $days = 30): array
    {
        $sql = "SELECT
                    COUNT(*) as total_breaks,
                    AVG(frequency_minutes) as avg_frequency,
                    enabled
                FROM break_reminder_settings
                WHERE user_id = :user_id
                AND created_at >= DATE_SUB(NOW(), INTERVAL :days DAY)";

        $stmt = $this->prepare($sql);
        $stmt->bindParam(':user_id', $userId, PDO::PARAM_INT);
        $stmt->bindParam(':days', $days, PDO::PARAM_INT);
        $stmt->execute();

        return $stmt->fetch(PDO::FETCH_ASSOC) ?: [
            'total_breaks' => 0,
            'avg_frequency' => 25,
            'enabled' => true
        ];
    }
}