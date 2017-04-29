"""
Add deleted column to shake table
"""

from yoyo import step

__depends__ = {'20170423_02_j66Zl-add-stripe-plan-id-to-user-table'}

steps = [
    step("ALTER TABLE `shake` ADD COLUMN `deleted` TINYINT(1) DEFAULT '0' AFTER `shake_category_id`"),
    step("UPDATE `shake` SET `deleted`=0 WHERE `deleted` IS NULL"),
    step("ALTER TABLE `shake` MODIFY COLUMN `deleted` TINYINT(1) NOT NULL DEFAULT '0'")
]
