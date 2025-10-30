"""Interface for database services."""

from typing import Any, Optional
from typing_extensions import Protocol


class IDatabaseService(Protocol):
    """Protocol defining the contract for database services."""

    def get_by_code_hash(self, code_hash: str) -> Optional[Any]:
        """
        Retrieve an analysis history record by code hash.

        Args:
            code_hash: The hash of the code snippet

        Returns:
            The database record if found, None otherwise
        """
        ...

    def create(
        self,
        *,
        code_hash: str,
        code_snippet: Optional[str],
        suggestions: list[dict[str, Any]],
        analysis_time_ms: Optional[int],
        language_version: Optional[str],
    ) -> Any:
        """
        Create a new analysis history record.

        Args:
            code_hash: The hash of the code snippet
            code_snippet: The original code snippet
            suggestions: List of analysis suggestions
            analysis_time_ms: Analysis duration in milliseconds
            language_version: Python version used

        Returns:
            The created database record
        """
        ...

