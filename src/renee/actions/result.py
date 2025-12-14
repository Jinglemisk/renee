"""ActionResult class for representing action execution outcomes.

Results capture the success/failure state, any errors, and events generated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from renee.actions.action import Action


@dataclass
class ActionResult:
    """Result of executing an action through the pipeline.

    Contains all information about the action execution:
    - Success/failure state
    - Cancellation status and reason
    - Error messages
    - Events generated during execution

    Attributes:
        success: Whether the action completed successfully
        action: The action that was executed
        cancelled: Whether the action was cancelled by rules
        cancel_reason: Reason for cancellation (if cancelled)
        error: Error message (if execution failed)
        events: Events generated during action execution

    Example:
        result = pipeline.execute(action, world)
        if result.success:
            for event in result.events:
                print(f"Event: {event}")
        elif result.cancelled:
            print(f"Cancelled: {result.cancel_reason}")
        else:
            print(f"Error: {result.error}")
    """

    success: bool
    action: Action
    cancelled: bool = False
    cancel_reason: str | None = None
    error: str | None = None
    events: list[Any] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Validate consistency
        if self.success and (self.cancelled or self.error):
            raise ValueError("Successful action cannot be cancelled or have errors")
        if self.cancelled and not self.cancel_reason:
            raise ValueError("Cancelled action must have a cancel_reason")
        if not self.success and not self.cancelled and not self.error:
            raise ValueError("Failed action must have either cancel_reason or error")

    @classmethod
    def success_result(cls, action: Action, events: list[Any] | None = None) -> ActionResult:
        """Create a successful action result.

        Args:
            action: The action that succeeded
            events: Events generated during execution

        Returns:
            ActionResult with success=True
        """
        return cls(
            success=True,
            action=action,
            events=events or []
        )

    @classmethod
    def cancelled_result(cls, action: Action, reason: str) -> ActionResult:
        """Create a cancelled action result.

        Args:
            action: The action that was cancelled
            reason: Reason for cancellation

        Returns:
            ActionResult with cancelled=True
        """
        return cls(
            success=False,
            action=action,
            cancelled=True,
            cancel_reason=reason
        )

    @classmethod
    def error_result(cls, action: Action, error: str) -> ActionResult:
        """Create an error action result.

        Args:
            action: The action that failed
            error: Error message

        Returns:
            ActionResult with success=False and error message
        """
        return cls(
            success=False,
            action=action,
            error=error
        )
