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
