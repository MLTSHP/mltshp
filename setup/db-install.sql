CREATE TABLE `sharedfile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `source_id` int(11) NOT NULL DEFAULT '0',
  `user_id` int(11) NOT NULL DEFAULT '0',
  `name` varchar(250) DEFAULT NULL,
  `title` varchar(250) DEFAULT NULL,
  `source_url` text,
  `description` text,
  `share_key` varchar(40) DEFAULT NULL,
  `content_type` varchar(128) DEFAULT NULL,
  `size` int(128) NOT NULL DEFAULT '0',
  `activity_at` datetime DEFAULT NULL,
  `parent_id` int(11) NOT NULL DEFAULT '0',
  `original_id` int(11) NOT NULL DEFAULT '0',
  `deleted` tinyint(1) NOT NULL DEFAULT '0',
  `like_count` mediumint(11) NOT NULL DEFAULT '0',
  `save_count` mediumint(11) NOT NULL DEFAULT '0',
  `view_count` int(11) unsigned NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `files_sharedfile_fbfc09f1` (`user_id`),
  KEY `original_id_deleted_idx` (`original_id`,`deleted`) USING BTREE,
  KEY `parent_id_deleted_idx` (`parent_id`,`deleted`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `sourcefile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `file_key` varchar(40) NOT NULL,
  `small_key` varchar(40) DEFAULT NULL,
  `thumb_key` varchar(40) DEFAULT NULL,
  `width` int(11) NOT NULL DEFAULT '0',
  `height` int(11) NOT NULL DEFAULT '0',
  `data` text,
  `type` enum('image','link') DEFAULT 'image',
  `nsfw` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `file_key_idx` (`file_key`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(30) DEFAULT NULL,
  `hashed_password` varchar(60) DEFAULT NULL,
  `email` varchar(128) DEFAULT NULL,
  `full_name` varchar(100) DEFAULT '',
  `about` varchar(255) DEFAULT '',
  `website` varchar(255) DEFAULT '',
  `profile_image` tinyint(1) DEFAULT '0',
  `invitation_count` tinyint(1) DEFAULT '0',
  `disable_notifications` tinyint(1) DEFAULT '0',
  `email_confirmed` tinyint(1) NOT NULL DEFAULT '0',
  `tou_agreed` tinyint(1) NOT NULL DEFAULT '0',
  `nsfw` tinyint(1) NOT NULL DEFAULT '0',
  `recommended` tinyint(1) NOT NULL DEFAULT '0',
  `is_paid` tinyint(1) NOT NULL DEFAULT '0',
  `deleted` tinyint(1) NOT NULL DEFAULT '0',
  `restricted` tinyint(1) NOT NULL DEFAULT '0',
  `show_naked_people` tinyint(1) NOT NULL DEFAULT '0',
  `show_stats` tinyint(1) NOT NULL DEFAULT '0',  
  `verify_email_token` varchar(40) DEFAULT NULL,
  `reset_password_token` varchar(40) DEFAULT NULL,
  `stripe_customer_id` varchar(40) DEFAULT NULL,
  `stripe_plan_id` varchar(40) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `invitation` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL DEFAULT '0',
  `claimed_by_user_id` int(11) NOT NULL DEFAULT '0',
  `invitation_key` varchar(40) DEFAULT NULL,
  `email_address` varchar(128) DEFAULT NULL,
  `name` varchar(128) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `claimed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `fileview` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL DEFAULT '0',
  `sharedfile_id` int(11) NOT NULL DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `sharedfile_id_idx` (`sharedfile_id`, `user_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `externalservice` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL DEFAULT '0',
  `service_id` int(11) NOT NULL DEFAULT '0',
  `screen_name` varchar(35) NOT NULL DEFAULT '',
  `type` tinyint(1) NOT NULL DEFAULT '0',
  `service_key` varchar(128) DEFAULT NULL,
  `service_secret` varchar(128) DEFAULT NULL,
  `deleted` tinyint(1) NOT NULL DEFAULT '0',  
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `favorite` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT '0',
  `sharedfile_id` int(11) DEFAULT '0',
  `deleted` tinyint(1) DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `sharedfile_id_user_id_unique_idx` (`sharedfile_id`,`user_id`),
  KEY `sharedfile_id_deleted_idx` (`sharedfile_id`,`deleted`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `shake` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT '0',
  `type` enum('user','group') DEFAULT 'user',
  `image` tinyint(1) DEFAULT '0',  
  `name` varchar(25) DEFAULT '',
  `title` varchar(128) DEFAULT NULL,
  `description` text,
  `recommended` tinyint(1) NOT NULL DEFAULT '0',
  `featured` tinyint(1) NOT NULL DEFAULT '0',
  `shake_category_id` INT(11) NOT NULL DEFAULT 0,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id_type_idx` (`user_id`, `type`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `subscription` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT '0',
  `shake_id` int(11) DEFAULT '0',
  `deleted` tinyint(1) DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id_shake_id_idx` (`user_id`,`shake_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `shakesharedfile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `shake_id` int(11) DEFAULT '0',
  `sharedfile_id` int(11) DEFAULT '0',
  `deleted` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `sharedfile_id_idx` (`sharedfile_id`) USING BTREE,
  KEY `shake_id_sharedfile_id_idx` (`shake_id`, `sharedfile_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `waitlist` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `email` varchar(128) DEFAULT NULL,
  `verification_key` varchar(40) DEFAULT NULL,
  `verified` tinyint(1) DEFAULT '0',
  `invited` tinyint(1) DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `comment` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT '0',
  `sharedfile_id` int(11) DEFAULT '0',
  `body` text,
  `deleted` tinyint(1) DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `sharedfile_id_idx` (`sharedfile_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `post` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT '0',
  `sourcefile_id` int(11) DEFAULT '0',
  `sharedfile_id` int(11) DEFAULT '0',
  `seen` tinyint(1) DEFAULT '0',
  `deleted` tinyint(1) DEFAULT '0',
  `shake_id` int(11) DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `usersrcdeleted_idx` (`user_id`,`sourcefile_id`, `deleted`) USING BTREE,
  KEY `sharedfile_idx` (`sharedfile_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `notification` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sender_id` int(11) DEFAULT '0',
  `receiver_id` int(11) DEFAULT '0',
  `action_id` int(11) DEFAULT '0',
  `type` enum('subscriber','favorite','save', 'comment', 'mention', 'invitation', 'invitation_request', 'invitation_approved', 'comment_like') DEFAULT NULL,
  `deleted` tinyint(1) DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `receiver_id_deleted_created_at_idx` (`receiver_id`,`deleted`,`created_at`) USING BTREE,
  KEY `receiver_id_type_deleted_idx` (`receiver_id`,`type`,`deleted`) USING BTREE,
  KEY `sender_id_deleted_idx` (`sender_id`, `deleted`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `app` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT '0',
  `title` text,
  `description` text,
  `secret` varchar(56) DEFAULT NULL,
  `redirect_url` text,
  `deleted` tinyint(1) DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `authorizationcode` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT '0',
  `app_id` int(11) DEFAULT '0',
  `code` varchar(40) DEFAULT NULL,
  `redeemed` tinyint(1) DEFAULT '0',
  `redirect_url` text,
  `expires_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `accesstoken` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT '0',
  `app_id` int(11) DEFAULT '0',
  `consumer_key` varchar(36) DEFAULT NULL,
  `consumer_secret` varchar(56) DEFAULT NULL,
  `deleted` tinyint(4) DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `apilog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `accesstoken_id` int(11) DEFAULT '0',
  `nonce` varchar(100) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `conversation` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT '0',
  `sharedfile_id` int(11) DEFAULT '0',
  `muted` tinyint(1) DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_sharedfile_idx` (`user_id`, `sharedfile_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `external_relationship` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT '0',
  `service_id` int(11) DEFAULT '0',
  `service_type` tinyint(1) DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id_service_type_service_id_idx` (`user_id`,`service_type`,`service_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `shake_manager` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `shake_id` int(11) NOT NULL DEFAULT '0',
  `user_id` int(11) NOT NULL DEFAULT '0',
  `deleted` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `payment_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL DEFAULT '0',  
  `status` varchar(128) DEFAULT NULL,
  `reference_id` varchar(128) DEFAULT NULL,
  `transaction_id` varchar(128) DEFAULT NULL,
  `operation` varchar(10) DEFAULT NULL,
  `transaction_date` datetime DEFAULT NULL,
  `next_transaction_date` datetime DEFAULT NULL,
  `buyer_email` varchar(128) DEFAULT NULL,
  `buyer_name` varchar(128) DEFAULT NULL,
  `recipient_email` varchar(128) DEFAULT NULL,
  `recipient_name` varchar(128) DEFAULT NULL,
  `payment_reason` varchar(128) DEFAULT NULL,
  `transaction_serial_number` int(128) NOT NULL DEFAULT '0',
  `subscription_id` varchar(128) DEFAULT NULL,
  `payment_method` varchar(10) DEFAULT NULL,
  `transaction_amount` varchar(128) DEFAULT NULL,
  `processor` tinyint(1) NOT NULL DEFAULT 0,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `bookmark` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT '0',
  `sharedfile_id` int(11) DEFAULT '0',
  `previous_sharedfile_id` int(11) DEFAULT '0',  
  `created_at` datetime DEFAULT NULL,
  UNIQUE KEY `user_id_created_at_idx` (`user_id`,`created_at`) USING BTREE,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `invitation_request` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL DEFAULT '0',
  `manager_id` int(11) NOT NULL DEFAULT '0',
  `shake_id` int(11) NOT NULL DEFAULT '0',
  `deleted` tinyint(1) NOT NULL DEFAULT '0',
  `updated_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `apihit` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `accesstoken_id` int(11) DEFAULT '0',
  `hits` int(11) NOT NULL DEFAULT '0',
  `hour_start` datetime DEFAULT NULL,
  UNIQUE KEY `accesstoken_id_hour_start_unique_idx` (`accesstoken_id`,`hour_start`),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `nsfw_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) not null DEFAULT '0',
  `sharedfile_id` int(11) not null DEFAULT '0',
  `sourcefile_id` int(11) not null DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `magicfile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sharedfile_id` int(11) NOT NULL DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  UNIQUE KEY `sharedfile_id` (`sharedfile_id`),
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `script_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) not null DEFAULT '',
  `result` text,
  `success` tinyint(1) NOT NULL DEFAULT '1',
  `started_at` datetime DEFAULT NULL,
  `finished_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `shake_category` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(128) DEFAULT NULL,
  `short_name` varchar(128) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `comment_like` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(128) DEFAULT '0',
  `comment_id` int(128) DEFAULT '0',
  `deleted` tinyint(1) DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `tag` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(20) NOT NULL DEFAULT '',
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `tag_name` (`name`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `tagged_file` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tag_id` int(11) DEFAULT '0',
  `sharedfile_id` int(11) DEFAULT NULL,
  `deleted` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4;

CREATE TABLE `promotion` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `name` varchar(128) DEFAULT NULL,
    `promotion_shake_id` int(11) NOT NULL DEFAULT 0,
    `membership_months` int(11) NOT NULL DEFAULT 0,
    `promotion_url` text,
    `expires_at` datetime default null,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `voucher` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `offered_by_user_id` int(11) NOT NULL DEFAULT 0,
  `claimed_by_user_id` int(11) NOT NULL DEFAULT 0,
  `voucher_key` varchar(40) DEFAULT NULL,
  `email_address` varchar(128) DEFAULT NULL,
  `name` varchar(128) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `claimed_at` datetime DEFAULT NULL,
  `promotion_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `voucher_key` (`voucher_key`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `migration_state` (
    `user_id` int(11) NOT NULL PRIMARY KEY,
    `is_migrated` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
