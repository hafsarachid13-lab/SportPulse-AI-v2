-- ============================================================
--  BASE DE DONNÉES — Agent IA Veille Sportive
--  Généré à partir des diagrammes de classes (Images 1 & 3),
--  use cases (Images 2 & 5) et ERD (Image 4)
--  Conflits résolus documentés dans les commentaires
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;
DROP DATABASE IF EXISTS veille_sportive;
CREATE DATABASE veille_sportive CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE veille_sportive;

-- ============================================================
-- 1. USERS
--    ERD + Diagramme 1 (Utilisateur) + Diagramme 2 (User)
--    Conflit résolu : rôle via ENUM au lieu de sous-classes
--    (Administrateur, Enseignant, Journaliste → enum)
-- ============================================================
CREATE TABLE users (
    id               INT           NOT NULL AUTO_INCREMENT,
    username         VARCHAR(100)  NOT NULL UNIQUE,
    email            VARCHAR(255)  NOT NULL UNIQUE,
    password_hash    VARCHAR(255)  NOT NULL,
    -- 2 rôles uniquement : admin et journaliste (regroupe étudiant/enseignant)
    role             ENUM('admin','journaliste') NOT NULL DEFAULT 'journaliste',
    is_active        BOOLEAN       NOT NULL DEFAULT TRUE,
    -- Champs supplémentaires de Diagramme 1
    niveau_acces     VARCHAR(50)   NULL,
    created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login       DATETIME      NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB;

-- ============================================================
-- 2. PERMISSIONS  (Diagramme 1 — classe Permission)
--    Absent de l'ERD mais présent dans Diag1 (## Sécurité & Logs)
-- ============================================================
CREATE TABLE permissions (
    id          INT           NOT NULL AUTO_INCREMENT,
    nom         VARCHAR(100)  NOT NULL,
    description VARCHAR(255)  NULL,
    niveau      INT           NOT NULL DEFAULT 1,
    PRIMARY KEY (id)
) ENGINE=InnoDB;

CREATE TABLE user_permissions (
    user_id       INT NOT NULL,
    permission_id INT NOT NULL,
    PRIMARY KEY (user_id, permission_id),
    FOREIGN KEY (user_id)       REFERENCES users(id)       ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 3. LOGS  (Diagramme 1 — classe Log)
--    Absent de l'ERD mais nécessaire (use case "Voir logs")
-- ============================================================
CREATE TABLE logs (
    id          INT           NOT NULL AUTO_INCREMENT,
    user_id     INT           NULL,
    action      VARCHAR(255)  NOT NULL,
    date_action DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details     TEXT          NULL,
    ip          VARCHAR(45)   NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================================
-- 4. SPORTS  (Diagramme 1 — classe Sport)
--    Absent de l'ERD, mais utilisé pour classifier les articles
-- ============================================================
CREATE TABLE sports (
    id         INT          NOT NULL AUTO_INCREMENT,
    nom        VARCHAR(100) NOT NULL UNIQUE,
    categorie  VARCHAR(100) NULL,
    popularite INT          NOT NULL DEFAULT 0,
    PRIMARY KEY (id)
) ENGINE=InnoDB;

-- ============================================================
-- 5. SOURCES  (ERD + Diagramme 1 & 2)
-- ============================================================
CREATE TABLE sources (
    id              INT           NOT NULL AUTO_INCREMENT,
    name            VARCHAR(255)  NOT NULL,
    url             TEXT          NOT NULL,
    feed_url        TEXT          NULL,
    -- Diag1 avait type implicite, Diag2 l'explicite
    type            ENUM('rss','api','scraping') NOT NULL DEFAULT 'rss',
    fiability_score FLOAT         NOT NULL DEFAULT 0,
    is_active       BOOLEAN       NOT NULL DEFAULT TRUE,
    last_checked    DATETIME      NULL,
    -- Ajouté par Diag1 : posteur de la source
    posted_by       INT           NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (posted_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================================
-- 6. SCHEDULER_TASKS  (ERD + Diagramme 2 — Scheduler)
-- ============================================================
CREATE TABLE scheduler_tasks (
    id              INT           NOT NULL AUTO_INCREMENT,
    job_name        VARCHAR(255)  NOT NULL,
    cron_expression VARCHAR(100)  NOT NULL,
    is_active       BOOLEAN       NOT NULL DEFAULT TRUE,
    last_run        DATETIME      NULL,
    next_run        DATETIME      NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB;

-- ============================================================
-- 7. COLLECT_JOBS  (ERD + Diagramme 2 — CollectJob)
-- ============================================================
CREATE TABLE collect_jobs (
    id                  INT          NOT NULL AUTO_INCREMENT,
    source_id           INT          NOT NULL,
    scheduler_id        INT          NULL,
    started_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at         DATETIME     NULL,
    articles_collected  INT          NOT NULL DEFAULT 0,
    status              ENUM('running','success','failed') NOT NULL DEFAULT 'running',
    error_message       TEXT         NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (source_id)    REFERENCES sources(id)          ON DELETE CASCADE,
    FOREIGN KEY (scheduler_id) REFERENCES scheduler_tasks(id)  ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================================
-- 8. ARTICLES  (ERD + Diagramme 1 & 2)
-- ============================================================
CREATE TABLE articles (
    id               INT           NOT NULL AUTO_INCREMENT,
    title            TEXT          NOT NULL,
    content          LONGTEXT      NULL,
    url              TEXT          NOT NULL,
    author           VARCHAR(255)  NULL,
    published_at     DATETIME      NULL,
    collected_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sport_category   VARCHAR(100)  NULL,
    -- Lien vers table sports (Diag1)
    sport_id         INT           NULL,
    importance_score FLOAT         NOT NULL DEFAULT 0.0,
    -- Diag1 : langue, imageURL, mots-clés
    langue           VARCHAR(10)   NOT NULL DEFAULT 'fr',
    image_url        TEXT          NULL,
    nb_mots          INT           NULL,
    -- Diag2 : status de vérification
    status           ENUM('pending','verified','rejected') NOT NULL DEFAULT 'pending',
    -- Diag1 : sentiment analysé
    sentiment        VARCHAR(50)   NULL,
    -- metadata JSON (Diag2)
    metadata         JSON          NULL,
    source_id        INT           NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_article_url (url(500)),
    FOREIGN KEY (source_id) REFERENCES sources(id)  ON DELETE CASCADE,
    FOREIGN KEY (sport_id)  REFERENCES sports(id)   ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================================
-- 9. REFERENCES  (Diagramme 1 — classe Reference)
--    Liens externes cités dans les articles — absent de l'ERD
-- ============================================================
CREATE TABLE references_ext (
    id              INT           NOT NULL AUTO_INCREMENT,
    article_id      INT           NOT NULL,
    titre           VARCHAR(255)  NULL,
    source          VARCHAR(255)  NULL,
    date_reference  DATE          NULL,
    lien_original   TEXT          NULL,
    nb_journaux     INT           NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 10. SUMMARIES  (ERD + Diagramme 2 — Summary + NLPProcessor)
-- ============================================================
CREATE TABLE summaries (
    id            INT          NOT NULL AUTO_INCREMENT,
    article_id    INT          NOT NULL,
    summary_text  TEXT         NOT NULL,
    generated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    model_used    VARCHAR(100) NOT NULL DEFAULT 'nlp-default',
    -- Diag2 : langue du résumé
    language      VARCHAR(10)  NOT NULL DEFAULT 'fr',
    PRIMARY KEY (id),
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 11. REVUES_DE_PRESSE  (ERD + Diag1 Synthese + Diag2 RevueDePresse)
--    Conflit résolu : fusion Synthese (Diag1) + RevueDePresse (Diag2/ERD)
--    Nom retenu : revues_de_presse (conforme ERD)
--    Champs retenus : union des deux classes
-- ============================================================
CREATE TABLE revues_de_presse (
    id              INT           NOT NULL AUTO_INCREMENT,
    date            DATE          NOT NULL UNIQUE,
    title           VARCHAR(500)  NOT NULL,
    content_json    JSON          NULL,
    -- Champs de Diag1 Synthese (absents de l'ERD mais utiles)
    periode_debut   DATE          NULL,
    periode_fin     DATE          NULL,
    format          VARCHAR(50)   NULL DEFAULT 'pdf',
    nb_articles     INT           NOT NULL DEFAULT 0,
    contenu_texte   LONGTEXT      NULL,
    -- Diag2 / ERD
    status          ENUM('draft','published') NOT NULL DEFAULT 'draft',
    generated_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id         INT           NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ============================================================
-- 12. REVUE_ITEMS  (ERD — table de jointure revue ↔ articles)
-- ============================================================
CREATE TABLE revue_items (
    id             INT           NOT NULL AUTO_INCREMENT,
    revue_id       INT           NOT NULL,
    article_id     INT           NOT NULL,
    rank           INT           NOT NULL DEFAULT 0,
    sport_section  VARCHAR(100)  NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_revue_article (revue_id, article_id),
    FOREIGN KEY (revue_id)   REFERENCES revues_de_presse(id) ON DELETE CASCADE,
    FOREIGN KEY (article_id) REFERENCES articles(id)         ON DELETE CASCADE
) ENGINE=InnoDB;


-- ============================================================
-- 14. ARCHIVES  (Diagramme 1 — classe Archive)
--    Absent de l'ERD, mais présent dans Diag1 et use case
-- ============================================================
CREATE TABLE archives (
    id             INT           NOT NULL AUTO_INCREMENT,
    source_id      INT           NULL,           -- article ou synthèse archivé
    revue_id       INT           NULL,
    date_archivage DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    type_contenu   VARCHAR(100)  NULL,
    contenu        LONGBLOB      NULL,           -- fichier binaire (PDF, etc.)
    taille         BIGINT        NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (source_id) REFERENCES articles(id)         ON DELETE SET NULL,
    FOREIGN KEY (revue_id)  REFERENCES revues_de_presse(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================================
-- 15. VERIFICATION  (Diagramme 1 — classe Verification)
--    L'ERD absorbe ça dans fiability_score de sources.
--    Conservé ici en table légère pour historique des checks IA
-- ============================================================
CREATE TABLE verifications (
    id                  INT     NOT NULL AUTO_INCREMENT,
    source_id           INT     NOT NULL,
    article_id          INT     NULL,
    date_verification   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    score_technique     FLOAT   NULL,
    score_contenu       FLOAT   NULL,
    score_correlation   FLOAT   NULL,
    score_final         FLOAT   NULL,
    statut              ENUM('valide','invalide','en_attente') NOT NULL DEFAULT 'en_attente',
    details             TEXT    NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (source_id)  REFERENCES sources(id)  ON DELETE CASCADE,
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- INDEX COMPLÉMENTAIRES
-- ============================================================
CREATE INDEX idx_articles_sport_id        ON articles(sport_id);
CREATE INDEX idx_articles_source_id       ON articles(source_id);
CREATE INDEX idx_articles_published_at    ON articles(published_at);
CREATE INDEX idx_articles_importance      ON articles(importance_score);
CREATE INDEX idx_collect_jobs_source      ON collect_jobs(source_id);
CREATE INDEX idx_summaries_article        ON summaries(article_id);
CREATE INDEX idx_revue_items_revue        ON revue_items(revue_id);
CREATE INDEX idx_revue_items_article      ON revue_items(article_id);
CREATE INDEX idx_logs_user_date           ON logs(user_id, date_action);
CREATE INDEX idx_statistics_period        ON statistics(period);
CREATE INDEX idx_verifications_source     ON verifications(source_id);

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- DONNÉES DE TEST MINIMALES
-- ============================================================

-- Sports de base
INSERT INTO sports (nom, categorie, popularite) VALUES
('Football',    'Collectif',   100),
('Basketball',  'Collectif',   90),
('Tennis',      'Individuel',  85),
('Rugby',       'Collectif',   75),
('Athlétisme',  'Individuel',  70);

-- Utilisateur admin par défaut
INSERT INTO users (username, email, password_hash, role, niveau_acces) VALUES
('admin', 'admin@veille-sport.fr', 'HASH_A_CHANGER', 'admin', 'full');

-- Permissions de base
INSERT INTO permissions (nom, description, niveau) VALUES
('VOIR_ARTICLES',   'Consulter les articles collectés',    1),
('POSTER_SOURCE',   'Ajouter une source de collecte',      2),
('GERER_USERS',     'Gérer les utilisateurs',              3),
('CONFIGURER_IA',   'Paramétrer l'agent IA',              3),
('VOIR_LOGS',       'Accéder aux logs système',            3),
('EXPORTER_PDF',    'Exporter les revues en PDF',          2);

-- ============================================================
-- FIN DU SCRIPT
-- ============================================================