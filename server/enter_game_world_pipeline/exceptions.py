"""
Exceptions for the enter game world pipeline handlers.
"""


class PipelineException(Exception):
    """Base exception for pipeline handler errors."""

    pass


class LoginException(PipelineException):
    """Exception raised when login packet handling fails."""

    pass


class AuthenticationException(PipelineException):
    """Exception raised when authentication fails."""

    pass


class CharacterDataException(PipelineException):
    """Exception raised when character data handling fails."""

    pass


class CharacterScreenException(PipelineException):
    """Exception raised when character screen interaction fails."""

    pass


class CharacterCreationException(PipelineException):
    """Exception raised when character creation fails."""

    pass


class EnterGameException(PipelineException):
    """Exception raised when entering game fails."""

    pass


class ServerCredentialsException(PipelineException):
    """Exception raised when sending server credentials fails."""

    pass


class StateTransitionException(PipelineException):
    """Exception raised when client state transition fails."""

    pass
