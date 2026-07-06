"""Authentication response schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from schemas.response.base_response import BaseResponse


class PatientResponse(BaseModel):
    """Patient profile data returned to the client."""

    model_config = ConfigDict(from_attributes=True)

    patient_id: Annotated[UUID, Field(description="Patient identifier")]
    dob: Annotated[date | None, Field(default=None, description="Date of birth")]
    gender: Annotated[str | None, Field(default=None, description="Patient gender")]
    height_cm: Annotated[Decimal | None, Field(default=None, description="Height in cm")]
    weight_kg: Annotated[Decimal | None, Field(default=None, description="Weight in kg")]


class UserData(BaseModel):
    """User account data returned after registration or lookup."""

    model_config = ConfigDict(from_attributes=True)

    user_id: Annotated[UUID, Field(description="User identifier")]
    full_name: Annotated[str, Field(description="User full name")]
    email: Annotated[str, Field(description="Email address used for login")]
    is_verified: Annotated[bool, Field(description="Whether the account is verified")]
    patient: Annotated[PatientResponse | None, Field(default=None, description="Linked patient profile")]


class UserResponse(BaseResponse[UserData]):
    """Standardized response envelope for user-centric auth endpoints."""


class TokenData(BaseModel):
    """JWT payload returned after login."""

    model_config = ConfigDict(from_attributes=True)

    access_token: Annotated[str, Field(description="Signed JWT access token")]
    token_type: Annotated[str, Field(description="Token type used by the Authorization header")]
    expires_in: Annotated[int, Field(description="Token lifetime in seconds")]
    user_id: Annotated[UUID, Field(description="User identifier encoded in the token")]
    patient_id: Annotated[UUID | None, Field(default=None, description="Patient identifier encoded in the token")]


class TokenResponse(BaseResponse[TokenData]):
    """Standardized response envelope for login."""


class LogoutResponse(BaseResponse[None]):
    """Standardized response envelope for logout."""
