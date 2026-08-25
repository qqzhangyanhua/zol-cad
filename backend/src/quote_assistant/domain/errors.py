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
