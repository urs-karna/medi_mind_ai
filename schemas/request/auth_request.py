"""Authentication request schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegisterRequest(BaseModel):
    """Register a new user and their linked patient profile."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, description="Email address used for login")
    password: str = Field(min_length=8, description="Raw password provided during signup")
    full_name: str = Field(min_length=1, description="Patient full name")
    gender: str | None = Field(default=None, description="Patient gender")
    date_of_birth: date | None = Field(default=None, description="Patient date of birth")
    height_cm: Decimal | None = Field(default=None, description="Height in centimetres (optional)")
    weight_kg: Decimal | None = Field(default=None, description="Weight in kilograms (optional)")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Keep login identifiers normalized so duplicate checks are consistent."""
        normalized_email = value.strip().lower()
        if "@" not in normalized_email or "." not in normalized_email.split("@")[-1]:
            raise ValueError("A valid email address is required")
        return normalized_email


class LoginRequest(BaseModel):
    """Authenticate an existing user account."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, description="Email address used for login")
    password: str = Field(min_length=1, description="Account password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Normalize emails so login matches the stored account exactly."""
        normalized_email = value.strip().lower()
        if "@" not in normalized_email or "." not in normalized_email.split("@")[-1]:
            raise ValueError("A valid email address is required")
        return normalized_email
