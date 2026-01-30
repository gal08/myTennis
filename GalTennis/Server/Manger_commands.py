"""
Gal Haham
Admin/manager privilege command handler.
Currently supports retrieving all users and their admin status.
NOW USES DBManager for all database operations.
"""
from Db_manager import get_db_manager

# Reference constants (for documentation)
ALLOWED_CATEGORIES = (
    'forehand',
    'backhand',
    'serve',
    'slice',
    'volley',
    'smash'
)
ALLOWED_DIFFICULTIES = ('easy', 'medium', 'hard')


class ManagerCommands:
    """
    Handles commands requiring manager/admin privileges using DBManager.
    Currently supports: GET_ALL_USERS.
    """

    def __init__(self):
        """Initialize with DBManager."""
        self.db = get_db_manager()

    def get_all_users(self, payload):
        """
        Retrieves a list of all users and their admin status using DBManager.
        NOTE: Server.py enforces the admin check before calling this method.
        """
        users = self.db.get_all_users()
        return {"status": "success", "users": users}

    def handle_request(self, request_type, payload):
        """Routes the manager request to the appropriate method."""
        if request_type == 'GET_ALL_USERS':
            return self.get_all_users(payload)
        else:
            return {
                "status": "error",
                "message": "Unknown manager command type."
            }