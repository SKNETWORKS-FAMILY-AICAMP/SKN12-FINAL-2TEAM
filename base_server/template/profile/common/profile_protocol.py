from .profile_serialize import (
    ProfileGetRequest, ProfileUpdateAllRequest, ProfileUpdateBasicRequest,
    ProfileUpdateNotificationRequest, ProfileChangePasswordRequest,
    ProfileGetPaymentPlanRequest, ProfileChangePlanRequest, 
    ProfileSaveApiKeysRequest, ProfileGetApiKeysRequest
)
from typing import Callable, Optional
import asyncio

class ProfileProtocol:
    def __init__(self):
        # 콜백 속성들
        self.on_profile_get_req_callback: Optional[Callable] = None
        self.on_profile_update_all_req_callback: Optional[Callable] = None
        self.on_profile_update_basic_req_callback: Optional[Callable] = None
        self.on_profile_update_notification_req_callback: Optional[Callable] = None
        self.on_profile_change_password_req_callback: Optional[Callable] = None
        self.on_profile_get_payment_plan_req_callback: Optional[Callable] = None
        self.on_profile_change_plan_req_callback: Optional[Callable] = None
        self.on_profile_save_api_keys_req_callback: Optional[Callable] = None
        self.on_profile_get_api_keys_req_callback: Optional[Callable] = None

    async def profile_get_req_controller(self, session, msg: bytes, length: int):
        request = ProfileGetRequest.model_validate_json(msg)
        if self.on_profile_get_req_callback:
            return await self.on_profile_get_req_callback(session, request)
        raise NotImplementedError('on_profile_get_req_callback is not set')

    async def profile_update_all_req_controller(self, session, msg: bytes, length: int):
        request = ProfileUpdateAllRequest.model_validate_json(msg)
        if self.on_profile_update_all_req_callback:
            return await self.on_profile_update_all_req_callback(session, request)
        raise NotImplementedError('on_profile_update_all_req_callback is not set')

    async def profile_update_basic_req_controller(self, session, msg: bytes, length: int):
        request = ProfileUpdateBasicRequest.model_validate_json(msg)
        if self.on_profile_update_basic_req_callback:
            return await self.on_profile_update_basic_req_callback(session, request)
        raise NotImplementedError('on_profile_update_basic_req_callback is not set')

    async def profile_update_notification_req_controller(self, session, msg: bytes, length: int):
        request = ProfileUpdateNotificationRequest.model_validate_json(msg)
        if self.on_profile_update_notification_req_callback:
            return await self.on_profile_update_notification_req_callback(session, request)
        raise NotImplementedError('on_profile_update_notification_req_callback is not set')

    async def profile_change_password_req_controller(self, session, msg: bytes, length: int):
        request = ProfileChangePasswordRequest.model_validate_json(msg)
        if self.on_profile_change_password_req_callback:
            return await self.on_profile_change_password_req_callback(session, request)
        raise NotImplementedError('on_profile_change_password_req_callback is not set')

    async def profile_get_payment_plan_req_controller(self, session, msg: bytes, length: int):
        request = ProfileGetPaymentPlanRequest.model_validate_json(msg)
        if self.on_profile_get_payment_plan_req_callback:
            return await self.on_profile_get_payment_plan_req_callback(session, request)
        raise NotImplementedError('on_profile_get_payment_plan_req_callback is not set')

    async def profile_save_api_keys_req_controller(self, session, msg: bytes, length: int):
        request = ProfileSaveApiKeysRequest.model_validate_json(msg)
        if self.on_profile_save_api_keys_req_callback:
            return await self.on_profile_save_api_keys_req_callback(session, request)
        raise NotImplementedError('on_profile_save_api_keys_req_callback is not set')

    async def profile_change_plan_req_controller(self, session, msg: bytes, length: int):
        request = ProfileChangePlanRequest.model_validate_json(msg)
        if self.on_profile_change_plan_req_callback:
            return await self.on_profile_change_plan_req_callback(session, request)
        raise NotImplementedError('on_profile_change_plan_req_callback is not set')

    async def profile_get_api_keys_req_controller(self, session, msg: bytes, length: int):
        request = ProfileGetApiKeysRequest.model_validate_json(msg)
        if self.on_profile_get_api_keys_req_callback:
            return await self.on_profile_get_api_keys_req_callback(session, request)
        raise NotImplementedError('on_profile_get_api_keys_req_callback is not set')