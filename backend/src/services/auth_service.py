from fastapi import HTTPException, status
from supabase import AsyncClient, AuthApiError
from src.schemas.auth import UserSignup, UserLogin, UserResponse, TokenPair
import logging


logger = logging.getLogger(__name__)

class AuthService:
    """Handles user authentication (signup, login, token refresh) via Supabase Auth."""
    
    def __init__(self, db: AsyncClient):
        self.db = db

    async def signup(
        self,
        user_data: UserSignup
    ) -> UserResponse:
        try:
            response = await self.db.auth.sign_up(
                {
                    "email": user_data.email,
                    "password": user_data.password,
                }
            )
            user = response.user
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="User creation failed unexpectedly.",
                )
            return UserResponse(
                id=user.id,
                email=user.email,
            )

        except AuthApiError as e:
            if e.code == "user_already_exists":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unable to create account. Please check your information and try again.",
                )

    async def login(
        self,
        credentials: UserLogin
    ) -> TokenPair:
        try:
            response = await self.db.auth.sign_in_with_password(
                {"email": credentials.email, "password": credentials.password}
            )

            session = response.session
            user = response.user

            if not session or not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Login failed due to an unexpected server error.",
                )

            return TokenPair(
                access_token=session.access_token,
                refresh_token=session.refresh_token,
            )

        except AuthApiError as e:
            logger.error(f"Supabase Auth Error during login: {e.message} | Status: {e.status}")
            if e.status == 400:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password.",
                )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.message,
            )

        except Exception as e:
            logger.exception(f"Unexpected system error during login : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal server error occurred."
            )

    async def refresh_access_token(
        self,
        refresh_token: str
    ) -> TokenPair:
        try:
            response = await self.db.auth.refresh_session(refresh_token)

            session = response.session
            user = response.user

            if not session or not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )

            return TokenPair(
                access_token=session.access_token,
                refresh_token=session.refresh_token,
            )
        except AuthApiError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to refresh token",
            )
