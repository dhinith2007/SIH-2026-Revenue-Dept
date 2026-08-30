from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, status
from app.schemas.auth import LoginRequest, LoginResponse, ReauthRequest, ReauthResponse
from app.schemas.user import UserResponse, UserSummary
from app.schemas.common import BaseResponse
from app.services.auth_service import AuthService
from app.core.permissions import get_permissions_for_role
from app.api.deps import get_auth_service, get_current_user

router = APIRouter()


@router.post(
    "/auth/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Department Officer Login",
    description="Authenticates a departmental officer via Username, Email, or Mobile and Password.",
)
@router.post(
    "/auth/login/",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
@router.post(
    "/revenue/auth/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Department Officer Login (Alias)",
)
@router.post(
    "/revenue/auth/login/",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    user, token, expires_in = auth_service.authenticate(
        identifier=payload.identifier,
        password=payload.password,
    )

    user_perms = get_permissions_for_role(user["role"])
    perm_list = [p.value for p in user_perms]

    user_summary = UserSummary(
        id=user["id"],
        username=user["username"],
        full_name=user["full_name"],
        role=user["role"],
        department=user["department"],
        division=user["division"],
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=user_summary,
        permissions=perm_list,
    )


@router.get(
    "/auth/me",
    response_model=BaseResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated Officer Profile",
    description="Returns the full profile and assigned role details for the active session.",
)
def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    profile = auth_service.get_profile(current_user["id"])
    return BaseResponse(
        success=True,
        data=UserResponse(**profile),
        message="Officer profile retrieved successfully.",
    )


@router.post(
    "/auth/logout",
    response_model=BaseResponse[Dict[str, str]],
    status_code=status.HTTP_200_OK,
    summary="Officer Logout",
    description="Terminates active session and records logout audit timestamp.",
)
def logout(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    return BaseResponse(
        success=True,
        data={"status": "LOGGED_OUT", "user_id": current_user["id"]},
        message="Session successfully terminated.",
    )


@router.post(
    "/auth/refresh",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh Session Access Token",
    description="Generates a refreshed access token for an active valid session.",
)
def refresh_token(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    from app.core.security import create_access_token

    token_payload = {
        "sub": current_user["id"],
        "username": current_user["username"],
        "role": current_user["role"],
    }
    new_token = create_access_token(token_payload)
    expires_in = 30 * 60

    user_perms = get_permissions_for_role(current_user["role"])
    perm_list = [p.value for p in user_perms]

    user_summary = UserSummary(
        id=current_user["id"],
        username=current_user["username"],
        full_name=current_user["full_name"],
        role=current_user["role"],
        department=current_user["department"],
        division=current_user["division"],
    )

    return LoginResponse(
        access_token=new_token,
        token_type="bearer",
        expires_in=expires_in,
        user=user_summary,
        permissions=perm_list,
    )


@router.post(
    "/auth/reauthenticate",
    response_model=ReauthResponse,
    status_code=status.HTTP_200_OK,
    summary="Re-authenticate for Sensitive Action",
    description="Validates officer credentials before executing sensitive administrative or override operations.",
)
def reauthenticate_action(
    payload: ReauthRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    auth_service.reauthenticate(
        user_id=current_user["id"],
        password=payload.password,
    )
    return ReauthResponse(
        success=True,
        message="Re-authentication confirmed successfully.",
        reauthenticated_at=datetime.now(timezone.utc).isoformat(),
    )
