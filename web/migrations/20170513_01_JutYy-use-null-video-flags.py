"""
Use NULL video flags
"""

from yoyo import step

__depends__ = {'20170509_01_bP9rC-add-disable-autoplay-column-to-user'}

steps = [
    step(
        "ALTER TABLE sourcefile MODIFY COLUMN webm_flag TINYINT(1) DEFAULT NULL",
        "ALTER TABLE sourcefile MODIFY COLUMN webm_flag TINYINT(1) DEFAULT 0",
    ),
    step(
        "ALTER TABLE sourcefile MODIFY COLUMN mp4_flag TINYINT(1) DEFAULT NULL",
        "ALTER TABLE sourcefile MODIFY COLUMN mp4_flag TINYINT(1) DEFAULT 0",
    ),
]
