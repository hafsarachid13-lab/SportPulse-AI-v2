from sqlalchemy.orm import Session

from backend.models.user import User


class UserRepository:
    @staticmethod
    def _default_username(email: str) -> str:
        return email.split("@", 1)[0]

    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    def get_by_username(self, db: Session, username: str) -> User | None:
        return db.query(User).filter(User.username == username).first()

    def get_by_id(self, db: Session, user_id: int) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    def list_users(self, db: Session) -> list[User]:
        return db.query(User).order_by(User.id.desc()).all()

    def delete(self, db: Session, user: User) -> None:
        db.delete(user)

    def save(self, db: Session, user: User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def create(
        self,
        db: Session,
        *,
        email: str,
        password_hash: str,
        username: str | None = None,
        role: str = "journaliste",
        commit: bool = True,
    ) -> User:
        user = User(
            username=username or self._default_username(email),
            email=email,
            password_hash=password_hash,
            role=role,
            is_active=True,
        )
        db.add(user)
        if commit:
            db.commit()
            db.refresh(user)
        else:
            db.flush()
        return user
