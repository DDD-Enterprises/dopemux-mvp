<?php

/**
 * Attention State History Model
 *
 * Manages historical attention state data for users.
 */

namespace Leantime\Plugins\Dopemux\Models;

use Leantime\Core\Db\Base as DbModel;

class AttentionStateHistory extends DbModel
{
    /**
     * Record attention state change
     */
    public function recordState($userId, $state, $context = null): bool
    {
        $sql = "INSERT INTO attention_state_history (user_id, state, context)
                VALUES (:user_id, :state, :context)";

        $stmt = $this->prepare($sql);
        $stmt->bindParam(':user_id', $userId, PDO::PARAM_INT);
        $stmt->bindParam(':state', $state, PDO::PARAM_STR);
        $stmt->bindParam(':context', $context, PDO::PARAM_STR);

        return $stmt->execute();
    }

    /**
     * Get attention state history for user
     */
    public function getUserHistory($userId, $limit = 50): array
    {
        $sql = "SELECT state, context, created_at
                FROM attention_state_history
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
     * Get most recent attention state for user
     */
    public function getCurrentState($userId): ?string
    {
        $sql = "SELECT state FROM attention_state_history
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 1";

        $stmt = $this->prepare($sql);
        $stmt->bindParam(':user_id', $userId, PDO::PARAM_INT);
        $stmt->execute();

        $result = $stmt->fetch(PDO::FETCH_ASSOC);
        return $result['state'] ?? null;
    }

    /**
     * Get attention state distribution for user
     */
    public function getStateDistribution($userId, $days = 30): array
    {
        $sql = "SELECT state, COUNT(*) as count
                FROM attention_state_history
                WHERE user_id = :user_id
                AND created_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
                GROUP BY state
                ORDER BY count DESC";

        $stmt = $this->prepare($sql);
        $stmt->bindParam(':user_id', $userId, PDO::PARAM_INT);
        $stmt->bindParam(':days', $days, PDO::PARAM_INT);
        $stmt->execute();

        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }
}