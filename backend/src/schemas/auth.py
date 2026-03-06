from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


def validate_password_strength(password: str) -> str:
    errors = []

    if not any(c.isupper() for c in password):
        errors.append("one uppercase letter")
    if not any(c.islower() for c in password):
        errors.append("one lowercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("one digit")
    if not any(not c.isalnum() for c in password):
        errors.append("one special character")

    if errors:
        raise ValueError(f"Password must contain: {', '.join(errors)}")

    return password


class UserSignup(BaseModel):
    email: EmailStr = Field(
        description="User unique email address", examples=["user@example.com"]
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="User password (8-128 characters)",
        examples=["SecurePass123!"],
    )

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class UserLogin(BaseModel):
    email: EmailStr = Field(
        description="User email address", examples=["user@example.com"]
    )
    password: str = Field(description="User password", examples=["SecurePass123!"])


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
