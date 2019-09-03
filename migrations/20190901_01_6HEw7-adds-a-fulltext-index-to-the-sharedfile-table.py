"""
Adds a FULLTEXT index to the sharedfile table.
"""

from yoyo import step

__depends__ = {'20170513_02_hJ1nf-add-stripe-plan-rate-column'}

steps = [
    step("alter table sharedfile add fulltext titledesc_fulltext_idx (title, description)")
]
