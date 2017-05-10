"""
Add video key columns to sourcefile
"""

from yoyo import step

__depends__ = {'20170429_01_0ad8s-add-deleted-column-to-shake-table'}

steps = [
    step(
        "ALTER TABLE sourcefile ADD COLUMN `webm_key` varchar(40) DEFAULT NULL AFTER `small_key`",
        "ALTER TABLE sourcefile DROP COLUMN `webm_key`",
    ),
    step(
        "ALTER TABLE sourcefile ADD COLUMN `mp4_key` varchar(40) DEFAULT NULL AFTER `small_key`",
        "ALTER TABLE sourcefile DROP COLUMN `mp4_key`",
    ),
]
