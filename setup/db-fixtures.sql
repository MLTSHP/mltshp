-- create some basic users and user shakes for our "Best of" posts to collect
-- hashed passwords are generated with sha1('password' + settings.auth_secret)
-- auth_secret for local testing: dummy-secret
INSERT INTO `user` (`name`, `disable_notifications`, `created_at`) VALUES ('mltshp', 1, now());
-- password for "admin" is "password" if you're using the local testing auth_secret key
INSERT INTO `user` (`name`, `hashed_password`, `email`, `full_name`, `email_confirmed`, `is_paid`, `stripe_plan_id`, `created_at`)
     VALUES ('admin', '9bbdccf408a2420e20fcd157c6315d5f77427c64', 'admin@example.com', 'Site Admin', 1, 1, 'mltshp-double', now());

INSERT INTO `shake` (`user_id`, `type`, `name`) VALUES (1, 'user', 'Best of MLTSHP');
INSERT INTO `shake` (`user_id`, `type`) VALUES (2, 'user');
