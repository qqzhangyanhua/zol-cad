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


class ExtractedFieldNotFound(DomainError):
    pass


class IncompleteReview(DomainError):
    """标记已复核 was refused because 需确认 items are still unfinished."""


class AdminRequired(DomainError):
    """管理员专属能力（全厂修正记录统计、处理耗时与人工基线）。"""


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
