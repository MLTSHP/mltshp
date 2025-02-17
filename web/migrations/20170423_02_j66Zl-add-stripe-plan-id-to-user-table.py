"""
Add stripe_plan_id column to user table
"""

from yoyo import step

__depends__ = {'20170423_01_TwSED-adds-a-migration-state-table'}

steps = [
    step(
        "ALTER TABLE `user` ADD COLUMN `stripe_plan_id` VARCHAR(40) NULL AFTER `stripe_customer_id`",
        "ALTER TABLE `user` DROP COLUMN `stripe_plan_id`"
    )
]
