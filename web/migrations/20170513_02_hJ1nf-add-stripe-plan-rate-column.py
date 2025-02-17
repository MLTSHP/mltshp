"""
Add stripe_plan_rate column
"""

from yoyo import step

__depends__ = {'20170513_01_JutYy-use-null-video-flags'}

steps = [
    step(
        "ALTER TABLE user ADD COLUMN `stripe_plan_rate` INT(11) NULL AFTER `stripe_plan_id`",
        "ALTER TABLE user DROP COLUMN `stripe_plan_rate`",
    )
]
