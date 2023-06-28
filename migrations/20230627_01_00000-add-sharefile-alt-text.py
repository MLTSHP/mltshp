"""
Add an alt_text column to sharedfile
"""

from yoyo import step

steps = [
    step("ALTER TABLE sharedfile ADD COLUMN alt_text TEXT AFTER description;")
]
