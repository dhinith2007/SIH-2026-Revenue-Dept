from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status
from app.schemas.user import UserResponse
from app.schemas.common import BaseResponse
from app.core.permissions import PermissionEnum
from app.repositories.user_repository import UserRepository
from app.api.deps import get_user_repository, require_permission

router = APIRouter()


@router.get(
    "/admin/users",
    response_model=BaseResponse[List[UserResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Department Personnel",
    description="Retrieves all registered Revenue Department officers. Restricted to Department Administrator.",
)
def list_department_users(
    user_repo: UserRepository = Depends(get_user_repository),
    current_user: Dict[str, Any] = Depends(require_permission(PermissionEnum.USER_MANAGE)),
):
    users = user_repo.list_all()
    user_responses = [UserResponse(**u) for u in users]
    return BaseResponse(
        success=True,
        data=user_responses,
        message="Department personnel records retrieved successfully.",
    )
