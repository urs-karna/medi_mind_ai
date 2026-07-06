"""Authentication business logic for MediMind AI."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app_logging.logger import get_logger
from config.constants import AUTH_TOKEN_TYPE_BEARER, DEFAULT_DATABASE_ERROR_MESSAGE
from config.settings import settings
from database.connection import get_engine
from database.session import SessionLocal
from exceptions.custom_exceptions import (
    AuthenticationException,
    DatabaseException,
    ValidationException,
)
from models.patient_model import Patient
from models.user_model import User
from schemas.request.auth_request import LoginRequest, RegisterRequest

logger = get_logger(__name__)

# Compatibility patch for passlib 1.7.4 when running with bcrypt >= 4.0.0
try:
    import bcrypt
    import passlib.handlers.bcrypt

    if not hasattr(bcrypt, "__about__"):
        bcrypt.__about__ = type("About", (), {"__version__": bcrypt.__version__})
    passlib.handlers.bcrypt._bcrypt = bcrypt
    passlib.handlers.bcrypt.detect_wrap_bug = lambda ident: False
except ImportError:
    pass

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Encapsulate authentication rules without FastAPI-specific types."""

    # ── Registration ─────────────────────────────────────────

    def register_user(
        self, request_data: RegisterRequest, request_id: str = ""
    ) -> dict[str, Any]:
        """Create a user and patient record in a single transaction."""
        session: Session = SessionLocal(bind=get_engine())
        try:
            # Duplicate email check
            existing = session.scalar(
                select(User).where(User.email == request_data.email)
            )
            if existing is not None:
                raise ValidationException(
                    "Email already exists", details={"email": request_data.email}
                )

            # Create user
            user = User(
                full_name=request_data.full_name,
                email=request_data.email,
                password_hash=pwd_context.hash(request_data.password),
                is_verified=False,
            )
            session.add(user)
            session.flush()

            # Create linked patient (height/weight are optional → nullable)
            patient = Patient(
                user_id=user.user_id,
                dob=request_data.date_of_birth,
                gender=request_data.gender,
                height_cm=request_data.height_cm,
                weight_kg=request_data.weight_kg,
            )
            session.add(patient)

            # Commit the transaction
            session.commit()
            session.refresh(user)
            session.refresh(patient)

            payload = self._serialize_user(user, patient)
            logger.info(
                "User registration completed",
                operation="register_user",
                request_id=request_id,
            )
            return payload

        except ValidationException:
            session.rollback()
            raise
        except Exception as exc:
            session.rollback()
            logger.error(
                "User registration failed",
                operation="register_user",
                request_id=request_id,
                error=str(exc),
            )
            raise DatabaseException(message=DEFAULT_DATABASE_ERROR_MESSAGE)
        finally:
            session.close()

    # ── Login ────────────────────────────────────────────────

    def authenticate_user(
        self, request_data: LoginRequest, request_id: str = ""
    ) -> dict[str, Any]:
        """Validate credentials and mint a signed JWT."""
        session: Session = SessionLocal(bind=get_engine())
        try:
            user = session.scalar(
                select(User).where(User.email == request_data.email)
            )
            if user is None or not pwd_context.verify(
                request_data.password, user.password_hash
            ):
                logger.warning(
                    "Invalid login attempt",
                    operation="authenticate_user",
                    request_id=request_id,
                    email=request_data.email,
                )
                raise AuthenticationException("Invalid email or password")

            # Fetch the linked patient to embed patient_id in the token
            patient = session.scalar(
                select(Patient).where(Patient.user_id == user.user_id)
            )
            patient_id = patient.patient_id if patient else None

            # Update last_login timestamp
            user.last_login = datetime.now(timezone.utc)
            session.commit()

            token = self._create_access_token(user.user_id, patient_id)
            payload = {
                "access_token": token,
                "token_type": AUTH_TOKEN_TYPE_BEARER,
                "expires_in": settings.access_token_expire_minutes * 60,
                "user_id": user.user_id,
                "patient_id": patient_id,
            }
            logger.info(
                "User authenticated",
                operation="authenticate_user",
                request_id=request_id,
            )
            return payload

        except AuthenticationException:
            raise
        except Exception as exc:
            logger.error(
                "Login failed",
                operation="authenticate_user",
                request_id=request_id,
                error=str(exc),
            )
            raise DatabaseException(message=DEFAULT_DATABASE_ERROR_MESSAGE)
        finally:
            session.close()

    # ── Current user ─────────────────────────────────────────

    def get_current_user(
        self, token: str, request_id: str = ""
    ) -> dict[str, Any]:
        """Decode the JWT and return the authenticated user profile."""
        session: Session = SessionLocal(bind=get_engine())
        try:
            try:
                payload = jwt.decode(
                    token,
                    settings.jwt_secret_key,
                    algorithms=[settings.jwt_algorithm],
                )
            except JWTError as exc:
                logger.warning(
                    "JWT validation failed",
                    operation="get_current_user",
                    request_id=request_id,
                )
                raise AuthenticationException("Invalid or expired token") from exc

            raw_user_id = payload.get("user_id") or payload.get("sub")
            if raw_user_id is None:
                raise AuthenticationException("Invalid or expired token")

            user_id = uuid.UUID(str(raw_user_id))
            user = session.get(User, user_id)
            if user is None:
                raise AuthenticationException("User not found")

            patient = session.scalar(
                select(Patient).where(Patient.user_id == user.user_id)
            )
            result = self._serialize_user(user, patient)
            logger.info(
                "Current user resolved",
                operation="get_current_user",
                request_id=request_id,
            )
            return result

        except AuthenticationException:
            raise
        except Exception as exc:
            logger.error(
                "User resolution failed",
                operation="get_current_user",
                request_id=request_id,
                error=str(exc),
            )
            raise DatabaseException(message=DEFAULT_DATABASE_ERROR_MESSAGE)
        finally:
            session.close()

    # ── Logout ───────────────────────────────────────────────

    def logout_user(self, request_id: str = "") -> None:
        """Return a confirmation payload for stateless JWT logout."""
        logger.info("Logout requested", operation="logout_user", request_id=request_id)
        return None

    # ── Private helpers ──────────────────────────────────────

    def _create_access_token(
        self, user_id: uuid.UUID, patient_id: uuid.UUID | None
    ) -> str:
        """Create a short-lived JWT that carries user and patient identifiers."""
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
        payload: dict[str, Any] = {
            "sub": str(user_id),
            "user_id": str(user_id),
            "patient_id": str(patient_id) if patient_id else None,
            "iat": datetime.now(timezone.utc).timestamp(),
            "exp": expires_at,
        }
        return jwt.encode(
            payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

    def _serialize_user(
        self, user: User, patient: Patient | None
    ) -> dict[str, Any]:
        """Convert ORM objects into a plain dictionary for response models."""
        return {
            "user_id": user.user_id,
            "full_name": user.full_name,
            "email": user.email,
            "is_verified": user.is_verified,
            "patient": None
            if patient is None
            else {
                "patient_id": patient.patient_id,
                "dob": patient.dob,
                "gender": patient.gender,
                "height_cm": patient.height_cm,
                "weight_kg": patient.weight_kg,
            },
        }