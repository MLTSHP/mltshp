"""
Creates the dmca_takedown table that is used to log DMCA takedown
actions. This table already exists in production, so is created conditionally,
but this adds a new column as well to support identifying the user who did
the takedown.
"""

from yoyo import step

__depends__ = {"20230627_01_J71Z3-add-sharefile-alt-text"}

steps = [
    step("""CREATE TABLE IF NOT EXISTS dmca_takedown
                (id int unsigned not null auto_increment primary key,
                 share_key varchar(40) not null,
                 source_id int unsigned not null,
                 comment text,
                 created_at datetime default null,
                 updated_at datetime default null,
                 processed tinyint default 0);"""),
    step("ALTER TABLE dmca_takedown ADD COLUMN admin_user_id int unsigned default 0;"),
]
