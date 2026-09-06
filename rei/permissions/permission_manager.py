from enum import Enum


class PermissionLevel(Enum):
    P0_READ_ONLY = 0
    P1_SAFE = 1
    P2_MODIFICATION = 2
    P3_DESTRUCTIVE = 3
    P4_CRITICAL = 4


class PermissionManager:
    def is_allowed(self, permission: PermissionLevel) -> bool:
        if permission in {
            PermissionLevel.P0_READ_ONLY,
            PermissionLevel.P1_SAFE,
        }:
            return True

        return False