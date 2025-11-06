<?php

/**
 * ADHD User Preferences Model
 *
 * Stores user-specific ADHD preferences and settings.
 */

namespace Leantime\Plugins\Dopemux\Models;

use Leantime\Core\Db\Base as DbModel;

class ADHDUserPreferences extends DbModel
{
    /**
     * Get user's ADHD preferences
     */
    public function getUserPreferences($userId): array
    {
        $sql = "SELECT * FROM adhd_user_preferences WHERE user_id = :user_id";
        $stmt = $this->prepare($sql);
        $stmt->bindParam(':user_id', $userId, PDO::PARAM_INT);
        $stmt->execute();

        $preferences = $stmt->fetch(PDO::FETCH_ASSOC);

        return $preferences ?: $this->getDefaultPreferences();
    }

    /**
     * Update user's ADHD preferences
     */
    public function updateUserPreferences($userId, $preferences): bool
    {
        $sql = "INSERT INTO adhd_user_preferences (user_id, preferences)
                VALUES (:user_id, :preferences)
                ON DUPLICATE KEY UPDATE preferences = VALUES(preferences)";

        $stmt = $this->prepare($sql);
        $stmt->bindParam(':user_id', $userId, PDO::PARAM_INT);
        $stmt->bindParam(':preferences', json_encode($preferences), PDO::PARAM_STR);

        return $stmt->execute();
    }

    /**
     * Get default ADHD preferences
     */
    private function getDefaultPreferences(): array
    {
        return [
            'attention_tracking' => true,
            'break_reminders' => true,
            'context_preservation' => true,
            'cognitive_load_display' => true,
            'notification_batching' => true,
            'gentle_mode' => true,
            'focus_duration' => 25,
            'break_duration' => 5
        ];
    }
}