"""
Exceptions for the enter game world pipeline handlers.
"""


class pipeline_exception(Exception):
    """Base exception for pipeline handler errors."""

    pass


class login_exception(pipeline_exception):
    """Exception raised when login packet handling fails."""

    pass


class authentication_exception(pipeline_exception):
    """Exception raised when authentication fails."""

    pass


class character_data_exception(pipeline_exception):
    """Exception raised when character data handling fails."""

    pass


class character_screen_exception(pipeline_exception):
    """Exception raised when character screen interaction fails."""

    pass


class character_creation_exception(pipeline_exception):
    """Exception raised when character creation fails."""

    pass


class enter_game_exception(pipeline_exception):
    """Exception raised when entering game fails."""

    pass


class server_credentials_exception(pipeline_exception):
    """Exception raised when sending server credentials fails."""

    pass


class state_transition_exception(pipeline_exception):
    """Exception raised when client state transition fails."""

    pass
