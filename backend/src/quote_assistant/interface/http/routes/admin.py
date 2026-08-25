from __future__ import annotations

from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from quote_assistant.domain.errors import (
    AdminRequired,
    DuplicateUsername,
    InvalidAccount,
    InvalidFactoryPreferences,
    TenantDeleteConfirmationInvalid,
    UserNotFound,
)
from quote_assistant.interface.http.deps import (
    get_create_quoter,
    get_delete_tenant_data,
    get_disable_quoter,
    get_export_tenant_data,
    get_get_factory_preferences,
    get_list_factory_accounts,
    get_list_factory_processing_records,
    get_list_risk_rules,
    get_replace_common_materials,
    get_replace_risk_label_priority,
    get_request_tenant_delete,
)
from quote_assistant.interface.http.schemas import (
    CommonMaterialsRequest,
    CreateQuoterRequest,
    FactoryAccountListResponse,
    FactoryAccountResponse,
    FactoryPreferencesResponse,
    FactoryProcessingRecordListResponse,
    RiskLabelPriorityRequest,
    RiskRuleListResponse,
    TenantDeleteChallengeResponse,
    TenantDeleteRequest,
    TenantDeleteResponse,
    to_factory_account_response,
    to_factory_preferences_response,
    to_factory_processing_record_response,
    to_risk_rule_response,
)
from quote_assistant.usecase.create_quoter import CreateQuoter
from quote_assistant.usecase.delete_tenant_data import DeleteTenantData
from quote_assistant.usecase.disable_quoter import DisableQuoter
from quote_assistant.usecase.export_tenant_data import ExportTenantData
from quote_assistant.usecase.get_factory_preferences import GetFactoryPreferences
from quote_assistant.usecase.list_factory_accounts import ListFactoryAccounts
from quote_assistant.usecase.list_factory_processing_records import ListFactoryProcessingRecords
from quote_assistant.usecase.list_risk_rules import ListRiskRules
from quote_assistant.usecase.replace_common_materials import ReplaceCommonMaterials
from quote_assistant.usecase.replace_risk_label_priority import ReplaceRiskLabelPriority
from quote_assistant.usecase.request_tenant_delete import RequestTenantDelete

router = APIRouter(tags=["admin"])


@router.get("/admin/accounts", response_model=FactoryAccountListResponse)
def list_factory_accounts(
    use_case: ListFactoryAccounts = Depends(get_list_factory_accounts),
) -> FactoryAccountListResponse:
    try:
        users = use_case.execute()
    except AdminRequired as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return FactoryAccountListResponse(items=[to_factory_account_response(user) for user in users])


@router.post("/admin/accounts", response_model=FactoryAccountResponse)
def create_quoter(
    payload: CreateQuoterRequest,
    use_case: CreateQuoter = Depends(get_create_quoter),
) -> FactoryAccountResponse:
    try:
        user = use_case.execute(payload.username, payload.password)
    except AdminRequired as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (InvalidAccount, DuplicateUsername) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return to_factory_account_response(user)


@router.post("/admin/accounts/{user_id}/disable", response_model=FactoryAccountResponse)
def disable_quoter(
    user_id: UUID,
    use_case: DisableQuoter = Depends(get_disable_quoter),
) -> FactoryAccountResponse:
    try:
        user = use_case.execute(user_id)
    except AdminRequired as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except UserNotFound as exc:
        raise HTTPException(status_code=404, detail="账号不存在") from exc
    except InvalidAccount as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return to_factory_account_response(user)


@router.get("/admin/processing-records", response_model=FactoryProcessingRecordListResponse)
def list_factory_processing_records(
    use_case: ListFactoryProcessingRecords = Depends(get_list_factory_processing_records),
) -> FactoryProcessingRecordListResponse:
    try:
        records = use_case.execute()
    except AdminRequired as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return FactoryProcessingRecordListResponse(
        items=[to_factory_processing_record_response(record) for record in records]
    )


@router.get("/factory-preferences", response_model=FactoryPreferencesResponse)
def get_factory_preferences(
    use_case: GetFactoryPreferences = Depends(get_get_factory_preferences),
) -> FactoryPreferencesResponse:
    return to_factory_preferences_response(use_case.execute())


@router.put("/admin/common-materials", response_model=FactoryPreferencesResponse)
def replace_common_materials(
    payload: CommonMaterialsRequest,
    use_case: ReplaceCommonMaterials = Depends(get_replace_common_materials),
) -> FactoryPreferencesResponse:
    try:
        prefs = use_case.execute(payload.materials)
    except AdminRequired as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except InvalidFactoryPreferences as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return to_factory_preferences_response(prefs)


@router.put("/admin/risk-label-priority", response_model=FactoryPreferencesResponse)
def replace_risk_label_priority(
    payload: RiskLabelPriorityRequest,
    use_case: ReplaceRiskLabelPriority = Depends(get_replace_risk_label_priority),
) -> FactoryPreferencesResponse:
    try:
        prefs = use_case.execute(payload.priority)
    except AdminRequired as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except InvalidFactoryPreferences as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return to_factory_preferences_response(prefs)


@router.get("/admin/risk-rules", response_model=RiskRuleListResponse)
def list_risk_rules(
    use_case: ListRiskRules = Depends(get_list_risk_rules),
) -> RiskRuleListResponse:
    try:
        rules = use_case.execute()
    except AdminRequired as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return RiskRuleListResponse(items=[to_risk_rule_response(rule) for rule in rules])


@router.get("/admin/tenant-data/export")
def export_tenant_data(
    use_case: ExportTenantData = Depends(get_export_tenant_data),
) -> Response:
    try:
        archive, content = use_case.execute()
    except AdminRequired as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    encoded = quote(archive.filename)
    return Response(
        content=content,
        media_type=archive.media_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )


@router.post("/admin/tenant-data/delete-challenge", response_model=TenantDeleteChallengeResponse)
def request_tenant_delete(
    use_case: RequestTenantDelete = Depends(get_request_tenant_delete),
) -> TenantDeleteChallengeResponse:
    try:
        challenge = use_case.execute()
    except AdminRequired as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return TenantDeleteChallengeResponse(
        confirm_token=challenge.token,
        confirm_phrase=challenge.required_phrase,
        expires_at=challenge.expires_at,
    )


@router.post("/admin/tenant-data/delete", response_model=TenantDeleteResponse)
def delete_tenant_data(
    payload: TenantDeleteRequest,
    use_case: DeleteTenantData = Depends(get_delete_tenant_data),
) -> TenantDeleteResponse:
    try:
        use_case.execute(payload.confirm_token, payload.confirm_phrase)
    except AdminRequired as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except TenantDeleteConfirmationInvalid as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TenantDeleteResponse()
