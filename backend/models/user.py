from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
	__tablename__ = "users"

	id = Column(Integer, primary_key=True, index=True)
	email = Column(String(255), unique=True, nullable=False, index=True)
	password_hash = Column(String(255), nullable=False)
	full_name = Column(String(255), nullable=True)
	role = Column(String(50), nullable=False, default="Student")
	is_active = Column(Boolean, nullable=False, default=True)

