-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 22, 2026 at 09:32 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `veille_sportive`
--

-- --------------------------------------------------------

--
-- Table structure for table `archives`
--

CREATE TABLE `archives` (
  `id` int(11) NOT NULL,
  `source_id` int(11) DEFAULT NULL,
  `revue_id` int(11) DEFAULT NULL,
  `date_archivage` datetime NOT NULL DEFAULT current_timestamp(),
  `type_contenu` varchar(100) DEFAULT NULL,
  `contenu` longblob DEFAULT NULL,
  `taille` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `articles`
--

CREATE TABLE `articles` (
  `id` int(11) NOT NULL,
  `title` text NOT NULL,
  `content` longtext DEFAULT NULL,
  `url` text NOT NULL,
  `author` varchar(255) DEFAULT NULL,
  `published_at` datetime DEFAULT NULL,
  `collected_at` datetime NOT NULL DEFAULT current_timestamp(),
  `sport_category` varchar(100) DEFAULT NULL,
  `sport_id` int(11) DEFAULT NULL,
  `importance_score` float NOT NULL DEFAULT 0,
  `langue` varchar(10) NOT NULL DEFAULT 'fr',
  `image_url` text DEFAULT NULL,
  `nb_mots` int(11) DEFAULT NULL,
  `status` enum('pending','verified','rejected') NOT NULL DEFAULT 'pending',
  `sentiment` varchar(50) DEFAULT NULL,
  `metadata` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`metadata`)),
  `source_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `collect_jobs`
--

CREATE TABLE `collect_jobs` (
  `id` int(11) NOT NULL,
  `source_id` int(11) NOT NULL,
  `scheduler_id` int(11) DEFAULT NULL,
  `started_at` datetime NOT NULL DEFAULT current_timestamp(),
  `finished_at` datetime DEFAULT NULL,
  `articles_collected` int(11) NOT NULL DEFAULT 0,
  `status` enum('running','success','failed') NOT NULL DEFAULT 'running',
  `error_message` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `logs`
--

CREATE TABLE `logs` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `action` varchar(255) NOT NULL,
  `date_action` datetime NOT NULL DEFAULT current_timestamp(),
  `details` text DEFAULT NULL,
  `ip` varchar(45) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `permissions`
--

CREATE TABLE `permissions` (
  `id` int(11) NOT NULL,
  `nom` varchar(100) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `niveau` int(11) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `references_ext`
--

CREATE TABLE `references_ext` (
  `id` int(11) NOT NULL,
  `article_id` int(11) NOT NULL,
  `titre` varchar(255) DEFAULT NULL,
  `source` varchar(255) DEFAULT NULL,
  `date_reference` date DEFAULT NULL,
  `lien_original` text DEFAULT NULL,
  `nb_journaux` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `revues_de_presse`
--

CREATE TABLE `revues_de_presse` (
  `id` int(11) NOT NULL,
  `date` date NOT NULL,
  `title` varchar(500) NOT NULL,
  `content_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`content_json`)),
  `periode_debut` date DEFAULT NULL,
  `periode_fin` date DEFAULT NULL,
  `format` varchar(50) DEFAULT 'pdf',
  `nb_articles` int(11) NOT NULL DEFAULT 0,
  `contenu_texte` longtext DEFAULT NULL,
  `status` enum('draft','published') NOT NULL DEFAULT 'draft',
  `generated_at` datetime NOT NULL DEFAULT current_timestamp(),
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `revue_items`
--

CREATE TABLE `revue_items` (
  `id` int(11) NOT NULL,
  `revue_id` int(11) NOT NULL,
  `article_id` int(11) NOT NULL,
  `rank` int(11) NOT NULL DEFAULT 0,
  `sport_section` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `scheduler_tasks`
--

CREATE TABLE `scheduler_tasks` (
  `id` int(11) NOT NULL,
  `job_name` varchar(255) NOT NULL,
  `cron_expression` varchar(100) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `last_run` datetime DEFAULT NULL,
  `next_run` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sources`
--

CREATE TABLE `sources` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `url` text NOT NULL,
  `feed_url` text DEFAULT NULL,
  `type` enum('rss','api','scraping') NOT NULL DEFAULT 'rss',
  `fiability_score` float NOT NULL DEFAULT 0.5,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `last_checked` datetime DEFAULT NULL,
  `posted_by` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sports`
--

CREATE TABLE `sports` (
  `id` int(11) NOT NULL,
  `nom` varchar(100) NOT NULL,
  `categorie` varchar(100) DEFAULT NULL,
  `popularite` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `sports`
--

INSERT INTO `sports` (`id`, `nom`, `categorie`, `popularite`) VALUES
(1, 'Football', 'Collectif', 100),
(2, 'Basketball', 'Collectif', 90),
(3, 'Tennis', 'Individuel', 85),
(4, 'Rugby', 'Collectif', 75),
(5, 'Athlétisme', 'Individuel', 70);

-- --------------------------------------------------------

--
-- Table structure for table `statistics`
--

CREATE TABLE `statistics` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `period` date NOT NULL,
  `total_articles` int(11) NOT NULL DEFAULT 0,
  `by_sport` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`by_sport`)),
  `type_stat` varchar(100) DEFAULT NULL,
  `valeur` float DEFAULT NULL,
  `metadata` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`metadata`)),
  `computed_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `summaries`
--

CREATE TABLE `summaries` (
  `id` int(11) NOT NULL,
  `article_id` int(11) NOT NULL,
  `summary_text` text NOT NULL,
  `generated_at` datetime NOT NULL DEFAULT current_timestamp(),
  `model_used` varchar(100) NOT NULL DEFAULT 'nlp-default',
  `language` varchar(10) NOT NULL DEFAULT 'fr'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(100) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('admin','journaliste') NOT NULL DEFAULT 'journaliste',
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `niveau_acces` varchar(50) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `last_login` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `username`, `email`, `password_hash`, `role`, `is_active`, `niveau_acces`, `created_at`, `last_login`) VALUES
(1, 'admin', 'admin@veille-sport.fr', 'HASH_A_CHANGER', 'admin', 1, 'full', '2026-04-20 15:11:39', NULL),
(15, 'Ahmed Benali', 'ahmed@isic.ma', 'b2c8376cb76d9d9d298b2d6c9ee480d8$c438d864e3e5dc2016783ce70a469ed06c838fbcb1f57ae3536da79bf4405705', 'admin', 1, NULL, '2026-04-20 20:12:48', NULL),
(16, 'Fatima Zahra', 'fatima@isic.ma', '5ed93868f2b03373ca628c50f465130d$c8834f908c18b59dc188e5fbe0641c431ce2b072dcabe2c11ca2b2962db8de10', 'journaliste', 1, NULL, '2026-04-20 20:12:48', NULL),
(28, 'hafsarachid13', 'hafsarachid13@gmail.com', '9ebb8add32e3a36245c0e9ff0fa2412b$8a4989eb446d9a3a9384a10b682183be89e2231d7ac56b82b084185d45931bde', 'admin', 1, NULL, '2026-04-20 20:49:41', NULL),
(29, 'simossnasiri', 'simossnasiri@gmail.com', '78f7d643721f4235f7b1bfa6a0ac594b$2fa85995f20bd17bc0f622d69ffde3c98c6a14924cee4e70088312cddaf6ba40', 'admin', 1, NULL, '2026-04-20 20:49:41', NULL),
(30, 'yahyabenjdy044', 'yahyabenjdy044@gmail.com', '77cd7a3bfa83e677ec7efe3f77e9fd0d$6affa606d70e033b0b41c92e144be91fb419344ce060b783a9511e3754d5d375', 'admin', 1, NULL, '2026-04-20 20:49:41', NULL),
(35, 'stagefablab26', 'stagefablab26@gmail.com', '361b1e9f1a3b1275e7ac75950925eb8e$6bb78244e81281ca3951b85bd5f2641ce91a260c5390214b7c297d4a9010c00f', 'admin', 1, NULL, '2026-04-21 00:11:03', NULL),
(36, 'meryemfsr', 'meryemfsr93@gmail.com', 'ae8658975e243745d66ca1eddecbd51c$3640e11779fa461bd12eafd309eff0c4ba5dbab83aa9e84a654308ce39af3c53', 'admin', 1, NULL, '2026-04-21 15:37:22', NULL),

-- --------------------------------------------------------

--
-- Table structure for table `user_permissions`
--

CREATE TABLE `user_permissions` (
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `verifications`
--

CREATE TABLE `verifications` (
  `id` int(11) NOT NULL,
  `source_id` int(11) NOT NULL,
  `article_id` int(11) DEFAULT NULL,
  `date_verification` datetime NOT NULL DEFAULT current_timestamp(),
  `score_technique` float DEFAULT NULL,
  `score_contenu` float DEFAULT NULL,
  `score_correlation` float DEFAULT NULL,
  `score_final` float DEFAULT NULL,
  `statut` enum('valide','invalide','en_attente') NOT NULL DEFAULT 'en_attente',
  `details` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `archives`
--
ALTER TABLE `archives`
  ADD PRIMARY KEY (`id`),
  ADD KEY `source_id` (`source_id`),
  ADD KEY `revue_id` (`revue_id`);

--
-- Indexes for table `articles`
--
ALTER TABLE `articles`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_article_url` (`url`(500)),
  ADD KEY `idx_articles_sport_id` (`sport_id`),
  ADD KEY `idx_articles_source_id` (`source_id`),
  ADD KEY `idx_articles_published_at` (`published_at`),
  ADD KEY `idx_articles_importance` (`importance_score`);

--
-- Indexes for table `collect_jobs`
--
ALTER TABLE `collect_jobs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `scheduler_id` (`scheduler_id`),
  ADD KEY `idx_collect_jobs_source` (`source_id`);

--
-- Indexes for table `logs`
--
ALTER TABLE `logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_logs_user_date` (`user_id`,`date_action`);

--
-- Indexes for table `permissions`
--
ALTER TABLE `permissions`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `references_ext`
--
ALTER TABLE `references_ext`
  ADD PRIMARY KEY (`id`),
  ADD KEY `article_id` (`article_id`);

--
-- Indexes for table `revues_de_presse`
--
ALTER TABLE `revues_de_presse`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `date` (`date`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `revue_items`
--
ALTER TABLE `revue_items`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_revue_article` (`revue_id`,`article_id`),
  ADD KEY `idx_revue_items_revue` (`revue_id`),
  ADD KEY `idx_revue_items_article` (`article_id`);

--
-- Indexes for table `scheduler_tasks`
--
ALTER TABLE `scheduler_tasks`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sources`
--
ALTER TABLE `sources`
  ADD PRIMARY KEY (`id`),
  ADD KEY `posted_by` (`posted_by`);

--
-- Indexes for table `sports`
--
ALTER TABLE `sports`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nom` (`nom`);

--
-- Indexes for table `statistics`
--
ALTER TABLE `statistics`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `idx_statistics_period` (`period`);

--
-- Indexes for table `summaries`
--
ALTER TABLE `summaries`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_summaries_article` (`article_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `user_permissions`
--
ALTER TABLE `user_permissions`
  ADD PRIMARY KEY (`user_id`,`permission_id`),
  ADD KEY `permission_id` (`permission_id`);

--
-- Indexes for table `verifications`
--
ALTER TABLE `verifications`
  ADD PRIMARY KEY (`id`),
  ADD KEY `article_id` (`article_id`),
  ADD KEY `idx_verifications_source` (`source_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `archives`
--
ALTER TABLE `archives`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `articles`
--
ALTER TABLE `articles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `collect_jobs`
--
ALTER TABLE `collect_jobs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `logs`
--
ALTER TABLE `logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `permissions`
--
ALTER TABLE `permissions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `references_ext`
--
ALTER TABLE `references_ext`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `revues_de_presse`
--
ALTER TABLE `revues_de_presse`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `revue_items`
--
ALTER TABLE `revue_items`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `scheduler_tasks`
--
ALTER TABLE `scheduler_tasks`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sources`
--
ALTER TABLE `sources`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sports`
--
ALTER TABLE `sports`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `statistics`
--
ALTER TABLE `statistics`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `summaries`
--
ALTER TABLE `summaries`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=38;

--
-- AUTO_INCREMENT for table `verifications`
--
ALTER TABLE `verifications`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `archives`
--
ALTER TABLE `archives`
  ADD CONSTRAINT `archives_ibfk_1` FOREIGN KEY (`source_id`) REFERENCES `articles` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `archives_ibfk_2` FOREIGN KEY (`revue_id`) REFERENCES `revues_de_presse` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `articles`
--
ALTER TABLE `articles`
  ADD CONSTRAINT `articles_ibfk_1` FOREIGN KEY (`source_id`) REFERENCES `sources` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `articles_ibfk_2` FOREIGN KEY (`sport_id`) REFERENCES `sports` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `collect_jobs`
--
ALTER TABLE `collect_jobs`
  ADD CONSTRAINT `collect_jobs_ibfk_1` FOREIGN KEY (`source_id`) REFERENCES `sources` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `collect_jobs_ibfk_2` FOREIGN KEY (`scheduler_id`) REFERENCES `scheduler_tasks` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `logs`
--
ALTER TABLE `logs`
  ADD CONSTRAINT `logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `references_ext`
--
ALTER TABLE `references_ext`
  ADD CONSTRAINT `references_ext_ibfk_1` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `revues_de_presse`
--
ALTER TABLE `revues_de_presse`
  ADD CONSTRAINT `revues_de_presse_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `revue_items`
--
ALTER TABLE `revue_items`
  ADD CONSTRAINT `revue_items_ibfk_1` FOREIGN KEY (`revue_id`) REFERENCES `revues_de_presse` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `revue_items_ibfk_2` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `sources`
--
ALTER TABLE `sources`
  ADD CONSTRAINT `sources_ibfk_1` FOREIGN KEY (`posted_by`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `statistics`
--
ALTER TABLE `statistics`
  ADD CONSTRAINT `statistics_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `summaries`
--
ALTER TABLE `summaries`
  ADD CONSTRAINT `summaries_ibfk_1` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `user_permissions`
--
ALTER TABLE `user_permissions`
  ADD CONSTRAINT `user_permissions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `user_permissions_ibfk_2` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `verifications`
--
ALTER TABLE `verifications`
  ADD CONSTRAINT `verifications_ibfk_1` FOREIGN KEY (`source_id`) REFERENCES `sources` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `verifications_ibfk_2` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
