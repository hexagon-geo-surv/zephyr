"""Exceptions for Robot Framework Twister integration."""

class RobotFrameworkTwisterError(Exception):
    """Base exception for Robot Framework Twister errors."""
    pass


class RobotTestNotFoundError(RobotFrameworkTwisterError):
    """Raised when Robot Framework test file is not found."""
    pass


class RobotExecutionError(RobotFrameworkTwisterError):
    """Raised when Robot Framework test execution fails."""
    pass


class RobotTimeoutError(RobotFrameworkTwisterError):
    """Raised when Robot Framework test times out."""
    pass
