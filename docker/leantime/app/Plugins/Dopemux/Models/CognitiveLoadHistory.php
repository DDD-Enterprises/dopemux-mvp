<?php

/**
 * Cognitive Load History Model
 *
 * Manages historical cognitive load data for users.
 */

namespace Leantime\Plugins\Dopemux\Models;

use Leantime\Core\Db\Base as DbModel;

class CognitiveLoadHistory extends DbModel
{
    /**
     * Record cognitive load measurement
     */
    public function recordLoad($userId, $loadValue, $context = null): bool
    {
        $sql = "INSERT INTO cognitive_load_history (user_id, load_value, context)
                VALUES (:user_id, :load_value, :context)";

        $stmt = $this->prepare($sql);
        $stmt->bindParam(':user_id', $userId, PDO::PARAM_INT);
        $stmt->bindParam(':load_value', $loadValue);
        $stmt->bindParam(':context', $context, PDO::PARAM_STR);

        return $stmt->execute();
    }

    /**
     * Get cognitive load history for user
     */
    public function getUserHistory($userId, $limit = 50): array
    {
        $sql = "SELECT load_value, context, created_at
                FROM cognitive_load_history
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT :limit";

        $stmt = $this->prepare($sql);
        $stmt->bindParam(':user_id', $userId, PDO::PARAM_INT);
        $stmt->bindParam(':limit', $limit, PDO::PARAM_INT);
        $stmt->execute();

        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }

    /**
     * Get average cognitive load for user over period
     */
    public function getAverageLoad($userId, $days = 7): float
    {
        $sql = "SELECT AVG(load_value) as avg_load
                FROM cognitive_load_history
                WHERE user_id = :user_id
                AND created_at >= DATE_SUB(NOW(), INTERVAL :days DAY)";

        $stmt = $this->prepare($sql);
        $stmt->bindParam(':user_id', $userId, PDO::PARAM_INT);
        $stmt->bindParam(':days', $days, PDO::PARAM_INT);
        $stmt->execute();

        $result = $stmt->fetch(PDO::FETCH_ASSOC);
        return (float) ($result['avg_load'] ?? 5.0);
    }

    /**
     * Clean old records (keep last 1000 per user)
     */
    public function cleanupOldRecords($userId): bool
    {
        $sql = "DELETE FROM cognitive_load_history
                WHERE user_id = :user_id
                AND id NOT IN (
                    SELECT id FROM (
                        SELECT id FROM cognitive_load_history
                        WHERE user_id = :user_id
                        ORDER BY created_at DESC
                        LIMIT 1000
                    ) temp
                )";

        $stmt = $this->prepare($sql);
        $stmt->bindParam(':user_id', $userId, PDO::PARAM_INT);

        return $stmt->execute();
    }
}