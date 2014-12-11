CREATE TABLE `int_project_backer` (
  `ts_id` varchar(100) NOT NULL DEFAULT '',
  `project_id` int(11) NOT NULL DEFAULT '0',
  `profile_url` varchar(1000) DEFAULT NULL,
  `backer_slug` varchar(400) DEFAULT NULL,
  `backing_hist` int(11) DEFAULT NULL,
  PRIMARY KEY (`ts_id`,`project_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8
/*!50100 PARTITION BY KEY ()
PARTITIONS 10 */;

CREATE TABLE `project_benchmark` (
  `project_id` int(11) NOT NULL,
  `project_name` varchar(1000) DEFAULT NULL,
  `project_slug` varchar(400) DEFAULT NULL,
  `country` varchar(100) DEFAULT NULL,
  `created_at_unix` int(11) DEFAULT NULL,
  `created_at_str` varchar(100) DEFAULT NULL,
  `project_url` varchar(1000) DEFAULT NULL,
  `desc_` mediumtext,
  `photo` varchar(2000) DEFAULT NULL,
  `category_parent` int(11) DEFAULT NULL,
  `category_name` varchar(255) DEFAULT NULL,
  `category_id` int(11) DEFAULT NULL,
  `launched_at_unix` int(11) DEFAULT NULL,
  `launched_at_str` varchar(100) DEFAULT NULL,
  `goal` float DEFAULT NULL,
  `currency` varchar(10) DEFAULT NULL,
  `backers` int(11) DEFAULT NULL,
  `pledged` float DEFAULT NULL,
  `state` varchar(50) DEFAULT NULL,
  `currently` int(11) DEFAULT NULL,
  `state_changed_unix` int(11) DEFAULT NULL,
  `state_changed_str` varchar(100) DEFAULT NULL,
  `deadline_unix` int(11) DEFAULT NULL,
  `deadline_str` varchar(100) DEFAULT NULL,
  `creator_id` int(11) DEFAULT NULL,
  `creator_url_slug` varchar(400) DEFAULT NULL,
  `creator_name` varchar(400) DEFAULT NULL,
  `creator_url_api` varchar(1000) DEFAULT NULL,
  `creator_url_web` varchar(1000) DEFAULT NULL,
  `location_country` varchar(200) DEFAULT NULL,
  `location_name` varchar(200) DEFAULT NULL,
  `location_slug` varchar(200) DEFAULT NULL,
  `location_nearby_api` varchar(1000) DEFAULT NULL,
  `location_nearby_web1` varchar(1000) DEFAULT NULL,
  `location_nearby_web2` varchar(1000) DEFAULT NULL,
  PRIMARY KEY (`project_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8
/*!50100 PARTITION BY KEY ()
PARTITIONS 5 */;

CREATE TABLE `project_benchmark_sub` (
  `ts_id` varchar(100) NOT NULL DEFAULT '',
  `project_id` int(11) NOT NULL DEFAULT '0',
  `project_reward_number` int(11) DEFAULT NULL,
  `project_reward_mim_money_list` varchar(1000) DEFAULT NULL,
  `project_reward_description_total_length` int(11) DEFAULT NULL,
  `project_reward_description_str` mediumtext,
  `image_count` int(11) DEFAULT NULL,
  `image_fnames_list` mediumtext,
  `description_length` int(11) DEFAULT NULL,
  `description_str` mediumtext,
  `risks_length` int(11) DEFAULT NULL,
  `risks_str` mediumtext,
  `video_has` smallint(6) DEFAULT NULL,
  `video_length` mediumint(9) DEFAULT NULL,
  `video_fname` varchar(1000) DEFAULT NULL,
  `video_has_high` smallint(6) DEFAULT NULL,
  `video_has_base` smallint(6) DEFAULT NULL,
  `facebook_like` int(11) DEFAULT NULL,
  PRIMARY KEY (`ts_id`,`project_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8
/*!50100 PARTITION BY KEY ()
PARTITIONS 10 */;

CREATE TABLE `project_history` (
  `ts_id` varchar(100) NOT NULL DEFAULT '',
  `project_id` int(11) NOT NULL DEFAULT '0',
  `backers` int(11) DEFAULT NULL,
  `pledged` float DEFAULT NULL,
  `state` text,
  `currently` int(11) DEFAULT NULL,
  `state_changed_unix` int(11) DEFAULT NULL,
  `state_changed_str` varchar(100) DEFAULT NULL,
  `deadline_unix` int(11) DEFAULT NULL,
  `deadline_str` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`ts_id`,`project_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8
/*!50100 PARTITION BY KEY ()
PARTITIONS 10 */;

CREATE TABLE `project_search_temp` (
  `ts_id` varchar(100) NOT NULL DEFAULT '',
  `project_id` int(11) NOT NULL DEFAULT '0',
  `project_url` varchar(1000) DEFAULT NULL,
  PRIMARY KEY (`ts_id`,`project_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
