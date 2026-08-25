from __future__ import annotations

from quote_assistant.domain.entities import Actor, FactoryProcessingRecord
from quote_assistant.usecase.ports import PartDrawingRepository, UserRepository
from quote_assistant.usecase.tenant import TenantBoundUseCase, require_admin


class ListFactoryProcessingRecords(TenantBoundUseCase):
    """管理员查看全厂零件图处理记录。报价员走默认的 actor 范围列表，不走这里。"""

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        users: UserRepository,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._users = users

    def execute(self) -> list[FactoryProcessingRecord]:
        require_admin(self.actor, "只有管理员可以查看全厂处理记录")
        names = {user.id: user.username for user in self._users.list_for_tenant(self.tenant)}
        records: list[FactoryProcessingRecord] = []
        for drawing in self._drawings.list_for_tenant(self.tenant):
            uploaded_by = drawing.uploaded_by_user_id
            records.append(
                FactoryProcessingRecord(
                    part_drawing_id=drawing.id,
                    original_filename=drawing.original_filename,
                    uploaded_at=drawing.uploaded_at,
                    status=drawing.status,
                    uploaded_by_user_id=uploaded_by,
                    uploaded_by_username=names.get(uploaded_by) if uploaded_by else None,
                    quote_task_id=drawing.quote_task_id,
                    quality_grade=drawing.quality_grade,
                )
            )
        return records
