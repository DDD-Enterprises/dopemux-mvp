class GitHubSpecialistError(Exception):
    """Base class for all GitHub Specialist errors."""
    pass


class RedactionError(GitHubSpecialistError):
    """Raised when a sensitive pattern is detected and output is blocked."""
    pass


class SchemaError(GitHubSpecialistError):
    """Raised when the model output does not match the expected JSON schema."""
    pass
