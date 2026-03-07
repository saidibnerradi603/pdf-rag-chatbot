from fastapi import APIRouter, Depends, status, Response, Request, HTTPException
from src.schemas.auth import UserSignup, UserLogin, TokenResponse, UserResponse
from src.services.auth_service import AuthService
from src.api.dependencies import get_current_user, get_auth_service
from typing import Dict

router = APIRouter()


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
)
async def signup(
    user: UserSignup, auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """
    Register a new user with an email address and a strong password.
    **Password requirements:**
    - Minimum 8 characters, maximum 128
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    **Returns:** The newly created user's `id` and `email`.
    """
    return await auth_service.signup(user)


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    credentials: UserLogin,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Authenticate with email and password.
    On success:
    - Returns a short-lived **JWT access token** in the response body.
    - Sets a long-lived **`refresh_token` HttpOnly cookie** (7-day TTL, scoped to `/api/v1/auth/refresh`).
    - Use the access token as a `Bearer` token in the `Authorization` header for all protected endpoints.
    """
    token_pair = await auth_service.login(credentials)

    response.set_cookie(
        key="refresh_token",
        value=token_pair.refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 60 * 60,
        path="/api/v1/auth/refresh",
    )

    return TokenResponse(access_token=token_pair.access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """ 
    Exchange the `refresh_token` HttpOnly cookie for a new **access token**.
    
    The existing refresh token is rotated — a new one is set in the cookie, and the old one is invalidated.  
    The cookie is read automatically by the browser; no body parameters are needed.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found"
        )

    token_pair = await auth_service.refresh_access_token(refresh_token)

    response.set_cookie(
        key="refresh_token",
        value=token_pair.refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 60 * 60,
        path="/api/v1/auth/refresh",
    )

    return TokenResponse(access_token=token_pair.access_token)


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """ 
    Returns the profile of the user identified by the Bearer token in the `Authorization` header.

    **Returns:** `id` and `email` of the authenticated user.    
    """
    return current_user


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response) -> Dict:
    """ 
    Clears the `refresh_token` HttpOnly cookie from the client.

    The access token on the client side should be discarded manually, as JWTs are stateless and cannot be revoked server-side.

    **Returns:** `{ "message": "Logged out successfully" }`
    """
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth/refresh",
        httponly=True,
        samesite="none",
        secure=True,
    )
    return {"message": "Logged out successfully"}
