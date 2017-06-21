-- create some basic users and user shakes for our "Best of" posts to collect
-- hashed passwords are generated with sha1('password' + settings.auth_secret)
-- auth_secret for local testing: dummy-secret
INSERT INTO `user` (`name`, `disable_notifications`, `created_at`) VALUES ('mltshp', 1, now());
-- password for "admin" is "password" if you're using the local testing auth_secret key
INSERT INTO `user` (`name`, `hashed_password`, `email`, `full_name`, `email_confirmed`, `is_paid`) VALUES ('admin', '9bbdccf408a2420e20fcd157c6315d5f77427c64', 'admin@example.com', 'Site Admin', 1, 1);

INSERT INTO `shake` (`user_id`, `type`, `name`) VALUES (1, 'user', 'Best of MLTSHP');
INSERT INTO `shake` (`user_id`, `type`) VALUES (2, 'user');

INSERT INTO `_yoyo_migration` (`id`, `ctime`) VALUES ('20170423_01_TwSED-adds-a-migration-state-table','2017-04-23 16:58:10');
INSERT INTO `_yoyo_migration` (`id`, `ctime`) VALUES ('20170423_02_j66Zl-add-stripe-plan-id-to-user-table','2017-04-28 06:28:14');
INSERT INTO `_yoyo_migration` (`id`, `ctime`) VALUES ('20170429_01_0ad8s-add-deleted-column-to-shake-table','2017-04-29 18:51:10');
INSERT INTO `_yoyo_migration` (`id`, `ctime`) VALUES ('20170507_01_mRphn-add-video-key-columns-to-sourcefile','2017-05-09 05:54:14');
INSERT INTO `_yoyo_migration` (`id`, `ctime`) VALUES ('20170509_01_bP9rC-add-disable-autoplay-column-to-user','2017-05-10 00:58:32');
INSERT INTO `_yoyo_migration` (`id`, `ctime`) VALUES ('20170513_01_JutYy-use-null-video-flags','2017-05-13 17:35:41');
INSERT INTO `_yoyo_migration` (`id`, `ctime`) VALUES ('20170513_02_hJ1nf-add-stripe-plan-rate-column','2017-05-13 23:37:37');
