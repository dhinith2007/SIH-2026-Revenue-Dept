from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from app.schemas.common import BaseResponse
from app.schemas.notification import (
    NotificationListResponse,
    NotificationItem,
    UnreadCountResponse,
    MarkReadResponse,
)
from app.services.notification_service import NotificationService
from app.api.deps import get_notification_service, get_current_user
from app.core.logging import logger

router = APIRouter()


@router.get(
    "/revenue/notifications",
    response_model=BaseResponse[NotificationListResponse],
    status_code=status.HTTP_200_OK,
    summary="List Departmental Notifications",
    description="Retrieves notifications tailored to current officer role with unread counts and severity levels.",
)
def list_notifications(
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    limit: int = Query(50, ge=1, le=100, description="Max notifications to retrieve"),
    notif_service: NotificationService = Depends(get_notification_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    role = current_user.get("role")
    res = notif_service.list_notifications(role=role, unread_only=unread_only, limit=limit)
    items = [NotificationItem(**it) for it in res["items"]]
    return BaseResponse(
        success=True,
        data=NotificationListResponse(
            items=items,
            total=res["total"],
            unread_count=res["unread_count"],
        ),
        message=f"Retrieved {len(items)} departmental notifications.",
    )


@router.get(
    "/revenue/notifications/unread-count",
    response_model=BaseResponse[UnreadCountResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Unread Notification Count",
)
def get_unread_count(
    notif_service: NotificationService = Depends(get_notification_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    role = current_user.get("role")
    count = notif_service.get_unread_count(role=role)
    return BaseResponse(
        success=True,
        data=UnreadCountResponse(unread_count=count),
        message=f"Current unread notification count: {count}",
    )


@router.post(
    "/revenue/notifications/{notification_id}/read",
    response_model=BaseResponse[MarkReadResponse],
    status_code=status.HTTP_200_OK,
    summary="Mark Single Notification as Read",
)
def mark_notification_read(
    notification_id: str,
    notif_service: NotificationService = Depends(get_notification_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    res = notif_service.mark_read(notification_id)
    return BaseResponse(
        success=True,
        data=MarkReadResponse(id=notification_id, read=True),
        message=f"Notification '{notification_id}' marked as read.",
    )


@router.post(
    "/revenue/notifications/mark-all-read",
    response_model=BaseResponse[Dict[str, int]],
    status_code=status.HTTP_200_OK,
    summary="Mark All Notifications as Read",
)
def mark_all_notifications_read(
    notif_service: NotificationService = Depends(get_notification_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    role = current_user.get("role")
    count = notif_service.mark_all_read(role=role)
    return BaseResponse(
        success=True,
        data={"marked_read_count": count},
        message=f"Marked {count} notifications as read.",
    )
