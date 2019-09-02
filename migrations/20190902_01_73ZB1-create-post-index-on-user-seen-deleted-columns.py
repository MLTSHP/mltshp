"""
Create post index on user, seen, deleted columns
"""

from yoyo import step

__depends__ = {'20190901_01_6HEw7-adds-a-fulltext-index-to-the-sharedfile-table'}

steps = [
    step("ALTER TABLE post ADD INDEX userseendeletedid_idx (user_id, seen, deleted, sharedfile_id);")
]
