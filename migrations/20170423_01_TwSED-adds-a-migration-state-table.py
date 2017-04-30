"""
Adds a migration_state table.
"""

from yoyo import step

__depends__ = {}

steps = [
    step("""
        CREATE TABLE migration_state (
            user_id int(11) NOT NULL PRIMARY KEY,
            is_migrated tinyint(1) NOT NULL DEFAULT '0'
        )
        """,
        """DROP TABLE migration_state""")
]
