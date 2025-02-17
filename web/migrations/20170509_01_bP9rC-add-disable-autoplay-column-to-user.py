"""
Add disable_autoplay column to user
"""

from yoyo import step

__depends__ = {'20170507_01_mRphn-add-video-key-columns-to-sourcefile'}

steps = [
    step(
        "ALTER TABLE user ADD COLUMN `disable_autoplay` tinyint(1) DEFAULT 0 AFTER `show_stats`",
        "ALTER TABLE user DROP COLUMN `disable_autoplay`",
    )
]
