"""
Some new indexes for performance
"""

from yoyo import step

__depends__ = {'20190902_01_73ZB1-create-post-index-on-user-seen-deleted-columns', '20250127_01_nF5uM-dmca-takedown-table'}

steps = [
    step("create index tag_id_idx on tagged_file (tag_id)"),
    step("create index sharedfile_id_idx on tagged_file (sharedfile_id)"),
    step("create index user_type_idx on externalservice (user_id, type)"),
    step("create index name_idx on shake (name)"),
    step("create index shake_idx on subscription (shake_id)"),
    step("create index user_id_idx on favorite (user_id, id)"),
]
