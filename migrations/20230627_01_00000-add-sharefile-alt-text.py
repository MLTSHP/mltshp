"""
Add an alt_text column to sharedfile
"""

from yoyo import step

steps = [
    step("ALTER TABLE sharedfile ADD COLUMN alt_text TEXT AFTER description;"),
    step("ALTER TABLE sharedfile DROP KEY titledesc_fulltext_idx;"),
    step("ALTER TABLE sharedfile ADD FULLTEXT KEY `titledesc_fulltext_idx` (`title`,`description`,`alt_text`);")
]
