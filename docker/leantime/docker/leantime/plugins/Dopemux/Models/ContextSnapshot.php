<?php

/**
 * Context Snapshot Model
 *
 * Manages context snapshots for users to save and restore work states.
 */

namespace Leantime\Plugins\Dopemux\Models;

use Leantime\Core\Db\Base as DbModel;

class ContextSnapshot extends DbModel
{
    /**
     * Save a context snapshot
     */
    public function saveSnapshot($userId, $name, $snapshotData): bool
    {
        $sql = "INSERT INTO context_snapshots (user_id, name, snapshot_data)
                VALUES (:user_id, :name, :snapshot_data)";

        $stmt = $this->prepare($sql);
        $stmt->bindParam(':user_id', $userId, PDO::PARAM_INT);
        $stmt->bindParam(':name', $name, PDO::PARAM_STR);
        $stmt->bindParam(':snapshot_data', json_encode($snapshotData), PDO::PARAM_STR);

        return $stmt->execute();
    }

    /**
     * Get context snapshots for user
     */
    public function getUserSnapshots($userId, $limit = 50): array
    {
        $sql = "SELECT id, name, snapshot_data, created_at
                FROM context_snapshots
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT :limit";

        $stmt = $this->prepare($sql);
        $stmt->bindParam(':user_id', $userId, PDO::PARAM_INT);
        $stmt->bindParam(':limit', $limit, PDO::PARAM_INT);
        $stmt->execute();

        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);

        // Decode JSON data
        foreach ($results as &$result) {
            $result['snapshot_data'] = json_decode($result['snapshot_data'], true);
        }

        return $results;
    }

    /**
     * Get specific context snapshot
     */
    public function getSnapshot($userId, $snapshotId): ?array
    {
        $sql = "SELECT id, name, snapshot_data, created_at
                FROM context_snapshots
                WHERE user_id = :user_id AND id = :snapshot_id";

        $stmt = $this->prepare($sql);
        $stmt->bindParam(':user_id', $userId, PDO::PARAM_INT);
        $stmt->bindParam(':snapshot_id', $snapshotId, PDO::PARAM_INT);
        $stmt->execute();

        $result = $stmt->fetch(PDO::FETCH_ASSOC);

        if ($result) {
            $result['snapshot_data'] = json_decode($result['snapshot_data'], true);
            return $result;
        }

        return null;
    }

    /**
     * Delete context snapshot
     */
    public function deleteSnapshot($userId, $snapshotId): bool
    {
        $sql = "DELETE FROM context_snapshots
                WHERE user_id = :user_id AND id = :snapshot_id";

        $stmt = $this->prepare($sql);
        $stmt->bindParam(':user_id', $userId, PDO::PARAM_INT);
        $stmt->bindParam(':snapshot_id', $snapshotId, PDO::PARAM_INT);

        return $stmt->execute();
    }

    /**
     * Clean old snapshots (keep last 20 per user)
     */
    public function cleanupOldSnapshots($userId): bool
    {
        $sql = "DELETE FROM context_snapshots
                WHERE user_id = :user_id
                AND id NOT IN (
                    SELECT id FROM (
                        SELECT id FROM context_snapshots
                        WHERE user_id = :user_id
                        ORDER BY created_at DESC
                        LIMIT 20
                    ) temp
                )";

        $stmt = $this->prepare($sql);
        $stmt->bindParam(':user_id', $userId, PDO::PARAM_INT);

        return $stmt->execute();
    }
}