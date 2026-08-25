class DomainError(Exception):
    """Base type for domain/use-case failures mapped by the interface layer."""


class InvalidCredentials(DomainError):
    pass


class Unauthenticated(DomainError):
    pass


class PartDrawingNotFound(DomainError):
    pass


class PdfUnreadable(DomainError):
    pass


class IllegalPartDrawingTransition(DomainError):
    pass


class ExtractionValidationFailed(DomainError):
    """Adapter-boundary schema rejected the engine payload. Dirty data must not enter the domain."""


class ExtractionEngineFailed(DomainError):
    """Adapter-mapped 提取引擎 failure. Use-case maps this to 提取失败 and keeps the retry path."""


class ExtractionTimeout(ExtractionEngineFailed):
    """Vendor transport timed out. Retryable."""


class ExtractionRateLimited(ExtractionEngineFailed):
    """Vendor transport returned a rate-limit. Retryable."""


class ExtractionTransportFailed(ExtractionEngineFailed):
    """Vendor transport failed (network / HTTP / protocol). Retryable."""


class ExtractionVendorNotConfigured(ExtractionEngineFailed):
    """票 02 / ADR-0009 has not selected a vendor. The skeleton must not call a paid API."""


class ExtractedFieldNotFound(DomainError):
    pass


class IncompleteReview(DomainError):
    """标记已复核 was refused because 需确认 items are still unfinished."""


class AdminRequired(DomainError):
    """管理员专属能力（账号、全厂记录、偏好配置、修正统计、处理耗时、本厂数据导出与删除、保密说明）。"""


class AccountDisabled(DomainError):
    """停用后的报价员账号不能再登录。"""


class DuplicateUsername(DomainError):
    """创建报价员时用户名已被占用。"""


class InvalidAccount(DomainError):
    """创建或停用账号的输入不合法。"""


class UserNotFound(DomainError):
    pass


class InvalidFactoryPreferences(DomainError):
    """本厂常用材料或风险标签优先级不合法。"""


class InvalidManualBaseline(DomainError):
    """管理员录入的人工基线不完整或数值不合法。"""


class InvalidQuoteTask(DomainError):
    """报价任务名称或客户名称不完整或不合法。"""


class QuoteTaskNotFound(DomainError):
    pass


class IncompleteQuoteTaskReview(DomainError):
    """导出报价底稿被拒绝，因为任务里还有未完成复核的零件图。"""


class InvalidQuoteSheetTemplate(DomainError):
    """工厂报价底稿模板配置不合法。后台 onboarding 配置，不进管理员界面。"""


class TenantDeleteConfirmationInvalid(DomainError):
    """删除本厂数据的二次确认 token 或短语不正确、已过期或已使用。"""
