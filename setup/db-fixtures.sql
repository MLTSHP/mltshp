-- create some basic users and user shakes for our "Best of" posts to collect
-- hashed passwords are generated with sha1('password' + settings.auth_secret)
-- auth_secret for local testing: ne4om9og3maw8orp2ot9quos5ed8aj3lam6up3ja
INSERT INTO `user` (`name`, `disable_notifications`, `created_at`) VALUES ('__best__', 1, now());
-- password for "admin" is "password" if you're using the local testing auth_secret key
INSERT INTO `user` (`name`, `hashed_password`, `email`, `full_name`, `email_confirmed`) VALUES ('admin', '24df745228013f7832b0ecced7313cd6b52db0c2', 'admin@example.com', 'Site Admin', 1);

INSERT INTO `shake` (`user_id`, `type`, `name`) VALUES (1, 'user', 'Best of MLTSHP');
INSERT INTO `shake` (`user_id`, `type`) VALUES (2, 'user');
