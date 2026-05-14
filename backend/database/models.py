from __future__ import annotations

from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


def _enum_values(enum_cls: type[PyEnum]) -> list[str]:
    return [member.value for member in enum_cls]


class UserRole(str, PyEnum):
    ADMIN = "admin"
    JOURNALISTE = "journaliste"


class SourceType(str, PyEnum):
    RSS = "rss"
    API = "api"
    SCRAPING = "scraping"


class CollectJobStatus(str, PyEnum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class ArticleStatus(str, PyEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class RevueStatus(str, PyEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


class VerificationStatus(str, PyEnum):
    VALIDE = "valide"
    INVALIDE = "invalide"
    EN_ATTENTE = "en_attente"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        Enum(UserRole, values_callable=_enum_values, native_enum=False),
        nullable=False,
        default=UserRole.JOURNALISTE.value,
    )
    is_active = Column(Boolean, nullable=False, default=True)
    niveau_acces = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    last_login = Column(DateTime, nullable=True)

    permission_links = relationship("UserPermission", back_populates="user", cascade="all, delete-orphan")
    logs = relationship("Log", back_populates="user")
    posted_sources = relationship("Source", back_populates="posted_by_user")
    revues = relationship("RevueDePresse", back_populates="user")
    statistics = relationship("Statistic", back_populates="user")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    niveau = Column(Integer, nullable=False, default=1)

    user_links = relationship("UserPermission", back_populates="permission", cascade="all, delete-orphan")


class UserPermission(Base):
    __tablename__ = "user_permissions"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)

    user = relationship("User", back_populates="permission_links")
    permission = relationship("Permission", back_populates="user_links")


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(255), nullable=False)
    date_action = Column(DateTime, nullable=False, server_default=func.now())
    details = Column(Text, nullable=True)
    ip = Column(String(45), nullable=True)

    user = relationship("User", back_populates="logs")


class Sport(Base):
    __tablename__ = "sports"

    id = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False, unique=True)
    categorie = Column(String(100), nullable=True)
    popularite = Column(Integer, nullable=False, default=0)

    articles = relationship("Article", back_populates="sport")


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    feed_url = Column(Text, nullable=True)
    type = Column(
        Enum(SourceType, values_callable=_enum_values, native_enum=False),
        nullable=False,
        default=SourceType.RSS.value,
    )
    fiability_score = Column(Float, nullable=False, default=0.5)
    is_active = Column(Boolean, nullable=False, default=True)
    last_checked = Column(DateTime, nullable=True)
    posted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    posted_by_user = relationship("User", back_populates="posted_sources")
    articles = relationship("Article", back_populates="source", cascade="all, delete-orphan")
    collect_jobs = relationship("CollectJob", back_populates="source", cascade="all, delete-orphan")
    verifications = relationship("Verification", back_populates="source", cascade="all, delete-orphan")


class SchedulerTask(Base):
    __tablename__ = "scheduler_tasks"

    id = Column(Integer, primary_key=True)
    job_name = Column(String(255), nullable=False)
    cron_expression = Column(String(100), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)

    collect_jobs = relationship("CollectJob", back_populates="scheduler")


class CollectJob(Base):
    __tablename__ = "collect_jobs"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    scheduler_id = Column(Integer, ForeignKey("scheduler_tasks.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(DateTime, nullable=False, server_default=func.now())
    finished_at = Column(DateTime, nullable=True)
    articles_collected = Column(Integer, nullable=False, default=0)
    status = Column(
        Enum(CollectJobStatus, values_callable=_enum_values, native_enum=False),
        nullable=False,
        default=CollectJobStatus.RUNNING.value,
    )
    error_message = Column(Text, nullable=True)

    source = relationship("Source", back_populates="collect_jobs")
    scheduler = relationship("SchedulerTask", back_populates="collect_jobs")


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    url = Column(Text, nullable=False)
    author = Column(String(255), nullable=True)
    published_at = Column(DateTime, nullable=True)
    collected_at = Column(DateTime, nullable=False, server_default=func.now())
    sport_category = Column(String(100), nullable=True)
    sport_id = Column(Integer, ForeignKey("sports.id", ondelete="SET NULL"), nullable=True)
    importance_score = Column(Float, nullable=False, default=0.0)
    credibility_score = Column(Float, nullable=False, default=0.75)
    langue = Column(String(10), nullable=False, default="fr")
    image_url = Column(Text, nullable=True)
    nb_mots = Column(Integer, nullable=True)
    status = Column(
        Enum(ArticleStatus, values_callable=_enum_values, native_enum=False),
        nullable=False,
        default=ArticleStatus.PENDING.value,
    )
    sentiment = Column(String(50), nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)

    source = relationship("Source", back_populates="articles")
    sport = relationship("Sport", back_populates="articles")
    references = relationship("ReferenceExt", back_populates="article", cascade="all, delete-orphan")
    summaries = relationship("Summary", back_populates="article", cascade="all, delete-orphan")
    revue_items = relationship("RevueItem", back_populates="article", cascade="all, delete-orphan")
    verifications = relationship("Verification", back_populates="article", cascade="all, delete-orphan")


class ReferenceExt(Base):
    __tablename__ = "references_ext"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    titre = Column(String(255), nullable=True)
    source = Column(String(255), nullable=True)
    date_reference = Column(Date, nullable=True)
    lien_original = Column(Text, nullable=True)
    nb_journaux = Column(Integer, nullable=False, default=0)

    article = relationship("Article", back_populates="references")


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    summary_text = Column(Text, nullable=False)
    generated_at = Column(DateTime, nullable=False, server_default=func.now())
    model_used = Column(String(100), nullable=False, default="nlp-default")
    language = Column(String(10), nullable=False, default="fr")

    article = relationship("Article", back_populates="summaries")


class RevueDePresse(Base):
    __tablename__ = "revues_de_presse"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    title = Column(String(500), nullable=False)
    content_json = Column(JSON, nullable=True)
    periode_debut = Column(Date, nullable=True)
    periode_fin = Column(Date, nullable=True)
    format = Column(String(50), nullable=True, default="pdf")
    nb_articles = Column(Integer, nullable=False, default=0)
    contenu_texte = Column(Text, nullable=True)
    status = Column(
        Enum(RevueStatus, values_callable=_enum_values, native_enum=False),
        nullable=False,
        default=RevueStatus.DRAFT.value,
    )
    generated_at = Column(DateTime, nullable=False, server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    user = relationship("User", back_populates="revues")
    items = relationship("RevueItem", back_populates="revue", cascade="all, delete-orphan")
    archives = relationship("Archive", back_populates="revue")


class RevueItem(Base):
    __tablename__ = "revue_items"
    __table_args__ = (UniqueConstraint("revue_id", "article_id", name="uq_revue_article"),)

    id = Column(Integer, primary_key=True)
    revue_id = Column(Integer, ForeignKey("revues_de_presse.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    rank = Column(Integer, nullable=False, default=0)
    sport_section = Column(String(100), nullable=True)

    revue = relationship("RevueDePresse", back_populates="items")
    article = relationship("Article", back_populates="revue_items")


class Statistic(Base):
    __tablename__ = "statistics"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    period = Column(Date, nullable=False, index=True)
    total_articles = Column(Integer, nullable=False, default=0)
    by_sport = Column(JSON, nullable=True)
    type_stat = Column(String(100), nullable=True)
    valeur = Column(Float, nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)
    computed_at = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship("User", back_populates="statistics")


class Archive(Base):
    __tablename__ = "archives"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("articles.id", ondelete="SET NULL"), nullable=True)
    revue_id = Column(Integer, ForeignKey("revues_de_presse.id", ondelete="SET NULL"), nullable=True)
    date_archivage = Column(DateTime, nullable=False, server_default=func.now())
    type_contenu = Column(String(100), nullable=True)
    contenu = Column(LargeBinary, nullable=True)
    taille = Column(BigInteger, nullable=True)

    source_article = relationship("Article")
    revue = relationship("RevueDePresse", back_populates="archives")


class Verification(Base):
    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=True)
    date_verification = Column(DateTime, nullable=False, server_default=func.now())
    score_technique = Column(Float, nullable=True)
    score_contenu = Column(Float, nullable=True)
    score_correlation = Column(Float, nullable=True)
    score_final = Column(Float, nullable=True)
    statut = Column(
        Enum(VerificationStatus, values_callable=_enum_values, native_enum=False),
        nullable=False,
        default=VerificationStatus.EN_ATTENTE.value,
    )
    details = Column(Text, nullable=True)

    source = relationship("Source", back_populates="verifications")
    article = relationship("Article", back_populates="verifications")


__all__ = [
    "Archive",
    "Article",
    "ArticleStatus",
    "Base",
    "CollectJob",
    "CollectJobStatus",
    "Log",
    "Permission",
    "ReferenceExt",
    "RevueDePresse",
    "RevueItem",
    "RevueStatus",
    "SchedulerTask",
    "Source",
    "SourceType",
    "Sport",
    "Statistic",
    "Summary",
    "User",
    "UserPermission",
    "UserRole",
    "Verification",
    "VerificationStatus",
]
