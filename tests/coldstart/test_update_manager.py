from dopemux.coldstart.rollback_manager import RollbackManager
from dopemux.coldstart.update_manager import UpdateConfig, UpdateManager, UpdateResult, VersionInfo
from dopemux.update.manager import (
    UpdateConfig as ExistingUpdateConfig,
    UpdateManager as ExistingUpdateManager,
    UpdateResult as ExistingUpdateResult,
    VersionInfo as ExistingVersionInfo,
)
from dopemux.update.rollback import RollbackManager as ExistingRollbackManager


def test_coldstart_update_manager_reexports_existing_update_types() -> None:
    assert UpdateManager is ExistingUpdateManager
    assert UpdateConfig is ExistingUpdateConfig
    assert UpdateResult is ExistingUpdateResult
    assert VersionInfo is ExistingVersionInfo


def test_coldstart_rollback_manager_reexports_existing_rollback_manager() -> None:
    assert RollbackManager is ExistingRollbackManager
