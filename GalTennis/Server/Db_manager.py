"""
Gal Haham
Database Manager - Centralized database operations for Tennis Social.
Handles all SQLite database interactions with proper connection management,
error handling, and query execution.
REFACTORED: Added constants for indices and strings, split long methods.
"""
import sqlite3
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

DB_NAME = 'users.db'
DB_TIMEOUT_SECONDS = 10

DEFAULT_IS_ADMIN = 0
DEFAULT_CONTENT_TYPE = 'text'
DEFAULT_LIKES_COUNT = 0

TABLE_USERS = 'users'
TABLE_VIDEOS = 'videos'
TABLE_COMMENTS = 'comments'
TABLE_LIKES = 'likes'
TABLE_STORIES = 'stories'

CATEGORY_FOREHAND = 'forehand'
CATEGORY_BACKHAND = 'backhand'
CATEGORY_SERVE = 'serve'
CATEGORY_SLICE = 'slice'
CATEGORY_VOLLEY = 'volley'
CATEGORY_SMASH = 'smash'

VIDEO_CATEGORIES = (
    CATEGORY_FOREHAND,
    CATEGORY_BACKHAND,
    CATEGORY_SERVE,
    CATEGORY_SLICE,
    CATEGORY_VOLLEY,
    CATEGORY_SMASH
)

DIFFICULTY_EASY = 'easy'
DIFFICULTY_MEDIUM = 'medium'
DIFFICULTY_HARD = 'hard'

VIDEO_DIFFICULTIES = (DIFFICULTY_EASY, DIFFICULTY_MEDIUM, DIFFICULTY_HARD)

CONTENT_TYPE_TEXT = 'text'
CONTENT_TYPE_IMAGE = 'image'
CONTENT_TYPE_VIDEO = 'video'

STORY_CONTENT_TYPES = (
    CONTENT_TYPE_TEXT,
    CONTENT_TYPE_IMAGE,
    CONTENT_TYPE_VIDEO,
)

STATUS_SUCCESS = "success"
STATUS_ERROR = "error"

MESSAGE_USER_CREATED = "User created successfully"
MESSAGE_USER_EXISTS = "Username already exists"
MESSAGE_VIDEO_ADDED = "Video added successfully"
MESSAGE_VIDEO_EXISTS = "Video already exists"
MESSAGE_COMMENT_ADDED = "Comment added successfully"
MESSAGE_LIKE_ADDED = "Video liked"
MESSAGE_LIKE_REMOVED = "Like removed"
MESSAGE_STORY_ADDED = "Story added successfully"

USER_ROW_ID = 0
USER_ROW_USERNAME = 1
USER_ROW_PASSWORD = 2
USER_ROW_IS_ADMIN = 3

USERS_LIST_USERNAME = 0
USERS_LIST_IS_ADMIN = 1

VIDEO_ROW_TITLE = 0
VIDEO_ROW_UPLOADER = 1
VIDEO_ROW_CATEGORY = 2
VIDEO_ROW_LEVEL = 3

COMMENT_ROW_USERNAME = 0
COMMENT_ROW_CONTENT = 1
COMMENT_ROW_TIMESTAMP = 2

STORY_ROW_USERNAME = 0
STORY_ROW_CONTENT_TYPE = 1
STORY_ROW_CONTENT = 2
STORY_ROW_FILENAME = 3
STORY_ROW_TIMESTAMP = 4

LIKE_EXISTS_QUERY = "SELECT 1 FROM likes WHERE username=? AND video_filename=?"
COUNT_LIKES_QUERY = "SELECT COUNT(*) FROM likes WHERE video_filename=?"
SINGLE_RESULT_INDEX = 0


class DBManager:
    """
    Centralized database manager for all Tennis Social database operations.

    Responsibilities:
    - Manage database connections with proper cleanup
    - Provide safe query execution with error handling
    - Initialize and maintain database schema
    - Offer convenience methods for common operations

    REFACTORED: All indices and strings extracted to constants.
    """

    def __init__(self, db_name: str = DB_NAME):
        """
        Initialize the database manager.

        Args:
            db_name: Name of the SQLite database file
        """
        self.db_name = db_name
        self._initialize_schema()

    @contextmanager
    def get_connection(self):
        """
        Context manager for safe database connections.
        Automatically handles connection cleanup.

        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")

        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_name, timeout=DB_TIMEOUT_SECONDS)
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def _initialize_schema(self):
        """
        Initialize all database tables with proper schema.
        Creates tables if they don't exist.
        REFACTORED: Split into separate methods for each table.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            self._create_users_table(cursor)
            self._create_videos_table(cursor)
            self._create_comments_table(cursor)
            self._create_likes_table(cursor)
            self._create_stories_table(cursor)

            conn.commit()

    def _create_users_table(self, cursor):
        """Create users table schema."""
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {TABLE_USERS} (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                username TEXT UNIQUE NOT NULL, 
                password TEXT NOT NULL, 
                is_admin INTEGER NOT NULL DEFAULT {DEFAULT_IS_ADMIN})''')

    def _create_videos_table(self, cursor):
        """Create videos table schema."""
        categories = ','.join([f"'{c}'" for c in VIDEO_CATEGORIES])
        difficulties = ','.join([f"'{d}'" for d in VIDEO_DIFFICULTIES])

        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {TABLE_VIDEOS} (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                filename TEXT UNIQUE NOT NULL, 
                uploader TEXT NOT NULL, 
                category TEXT NOT NULL 
                    CHECK(category IN ({categories})), 
                difficulty TEXT NOT NULL 
                    CHECK(difficulty IN ({difficulties})), 
                timestamp REAL NOT NULL, 
                FOREIGN KEY (uploader) REFERENCES {TABLE_USERS}(username))''')

    def _create_comments_table(self, cursor):
        """Create comments table schema."""
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {TABLE_COMMENTS} (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                video_filename TEXT NOT NULL, 
                username TEXT NOT NULL, 
                content TEXT NOT NULL, 
                timestamp TEXT NOT NULL, 
                FOREIGN KEY (video_filename) REFERENCES {TABLE_VIDEOS}(filename), 
                FOREIGN KEY (username) REFERENCES {TABLE_USERS}(username))''')

    def _create_likes_table(self, cursor):
        """Create likes table schema."""
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {TABLE_LIKES} (
                video_filename TEXT NOT NULL, 
                username TEXT NOT NULL, 
                FOREIGN KEY (username) REFERENCES {TABLE_USERS}(username), 
                FOREIGN KEY (video_filename) REFERENCES {TABLE_VIDEOS}(filename), 
                UNIQUE (video_filename, username))''')

    def _create_stories_table(self, cursor):
        """Create stories table schema."""
        content_types = ','.join([f"'{ct}'" for ct in STORY_CONTENT_TYPES])

        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {TABLE_STORIES} (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                username TEXT NOT NULL, 
                content_type TEXT NOT NULL
                    DEFAULT '{DEFAULT_CONTENT_TYPE}'
                    CHECK(content_type IN ({content_types})), 
                content TEXT NOT NULL, 
                filename TEXT, 
                timestamp TEXT NOT NULL, 
                FOREIGN KEY (username) REFERENCES {TABLE_USERS}(username))''')

    def execute_query(
        self,
        query: str,
        params: tuple = (),
        fetch_one: bool = False,
        fetch_all: bool = True
    ) -> Optional[Any]:
        """
        Execute a query with proper error handling.

        Args:
            query: SQL query to execute
            params: Query parameters
            fetch_one: If True, fetch single result
            fetch_all: If True, fetch all results

        Returns:
            Query results or None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()

                if fetch_one:
                    return cursor.fetchone()
                if fetch_all:
                    return cursor.fetchall()
                return None
        except Exception as e:
            print(f"Database error: {e}")
            return None

    def execute_many(self, query: str, params_list: List[tuple]) -> bool:
        """
        Execute a query multiple times with different parameters.

        Args:
            query: SQL query to execute
            params_list: List of parameter tuples

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                return True
        except Exception as e:
            print(f"Database error: {e}")
            return False

    def create_user(
        self,
        username: str,
        password: str,
        is_admin: int = DEFAULT_IS_ADMIN
    ) -> Dict[str, str]:
        """
        Create a new user in the database.

        Args:
            username: Username
            password: Password
            is_admin: Admin status (1 or 0)

        Returns:
            Dict with status and message
        """
        try:
            query = f'''
                INSERT INTO {TABLE_USERS} (username, password, is_admin)
                VALUES (?, ?, ?)
            '''
            self.execute_query(
                query,
                (username, password, is_admin),
                fetch_all=False
            )
            return {
                "status": STATUS_SUCCESS,
                "message": MESSAGE_USER_CREATED
            }
        except sqlite3.IntegrityError:
            return {"status": STATUS_ERROR, "message": MESSAGE_USER_EXISTS}
        except Exception as e:
            return {"status": STATUS_ERROR, "message": str(e)}

    def get_user(self, username: str, password: str) -> Optional[Tuple]:
        """
        Get user by username and password.

        Args:
            username: Username to search
            password: Password to verify

        Returns:
            Tuple of (id, username, password, is_admin) or None
        """
        query = f"SELECT * FROM {TABLE_USERS} WHERE username=? AND password=?"
        return self.execute_query(query, (username, password), fetch_one=True)

    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users (username and admin status only).

        Returns:
            List of user dictionaries
        """
        query = f"SELECT username, is_admin FROM {TABLE_USERS}"
        rows = self.execute_query(query)

        if not rows:
            return []

        return [
            {
                "username": row[USERS_LIST_USERNAME],
                "is_admin": row[USERS_LIST_IS_ADMIN]
            }
            for row in rows
        ]

    def add_video(
        self,
        filename: str,
        uploader: str,
        category: str,
        difficulty: str,
        timestamp: float
    ) -> Dict[str, str]:
        """
        Add a new video to the database.

        Args:
            filename: Video filename
            uploader: Username of uploader
            category: Video category
            difficulty: Difficulty level
            timestamp: Upload timestamp

        Returns:
            Dict with status and message
        """
        try:
            query = f'''
                INSERT INTO {TABLE_VIDEOS}
                (filename, uploader, category, difficulty, timestamp)
                VALUES (?, ?, ?, ?, ?)
            '''
            self.execute_query(
                query,
                (filename, uploader, category, difficulty, timestamp),
                fetch_all=False
            )
            return {
                "status": STATUS_SUCCESS,
                "message": MESSAGE_VIDEO_ADDED
            }
        except sqlite3.IntegrityError:
            return {"status": STATUS_ERROR, "message": MESSAGE_VIDEO_EXISTS}
        except Exception as e:
            return {"status": STATUS_ERROR, "message": str(e)}

    def get_all_videos(self) -> List[Dict[str, Any]]:
        """
        Get all videos with metadata.

        Returns:
            List of video dictionaries
        """
        query = f'''
            SELECT filename, uploader, category, difficulty
            FROM {TABLE_VIDEOS}
        '''
        rows = self.execute_query(query)

        if not rows:
            return []

        return [
            {
                "title": row[VIDEO_ROW_TITLE],
                "uploader": row[VIDEO_ROW_UPLOADER],
                "category": row[VIDEO_ROW_CATEGORY],
                "level": row[VIDEO_ROW_LEVEL],
            }
            for row in rows
        ]

    def add_comment(
        self,
        video_filename: str,
        username: str,
        content: str,
        timestamp: str
    ) -> Dict[str, str]:
        """
        Add a comment to a video.

        Args:
            video_filename: Video filename
            username: Commenter username
            content: Comment text
            timestamp: Comment timestamp

        Returns:
            Dict with status and message
        """
        try:
            query = f'''
                INSERT INTO {TABLE_COMMENTS}
                (video_filename, username, content, timestamp)
                VALUES (?, ?, ?, ?)
            '''
            self.execute_query(
                query,
                (video_filename, username, content, timestamp),
                fetch_all=False
            )
            return {
                "status": STATUS_SUCCESS,
                "message": MESSAGE_COMMENT_ADDED
            }
        except Exception as e:
            return {"status": STATUS_ERROR, "message": str(e)}

    def get_comments(self, video_filename: str) -> List[Dict[str, Any]]:
        """
        Get all comments for a video.

        Args:
            video_filename: Video filename

        Returns:
            List of comment dictionaries
        """
        query = f'''
            SELECT username, content, timestamp
            FROM {TABLE_COMMENTS}
            WHERE video_filename=?
            ORDER BY timestamp DESC
        '''
        rows = self.execute_query(query, (video_filename,))

        if not rows:
            return []

        return [
            {
                "username": row[COMMENT_ROW_USERNAME],
                "content": row[COMMENT_ROW_CONTENT],
                "timestamp": row[COMMENT_ROW_TIMESTAMP]
            }
            for row in rows
        ]

    def toggle_like(
        self,
        video_filename: str,
        username: str
    ) -> Dict[str, Any]:
        """
        Toggle like status for a video (add if not exists, remove if exists).
        REFACTORED: Split into helper methods.

        Args:
            video_filename: Video filename
            username: User's username

        Returns:
            Dict with status, message, and is_liked flag
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Check if like exists
                if self._like_exists(cursor, username, video_filename):
                    return self._remove_like(
                        conn,
                        cursor,
                        username,
                        video_filename,
                    )
                else:
                    return self._add_like(
                        conn,
                        cursor,
                        username,
                        video_filename,
                    )

        except Exception as e:
            return {"status": STATUS_ERROR, "message": str(e)}

    def _like_exists(self, cursor, username: str, video_filename: str) -> bool:
        """Check if a like already exists."""
        cursor.execute(LIKE_EXISTS_QUERY, (username, video_filename))
        return cursor.fetchone() is not None

    def _remove_like(
        self,
        conn,
        cursor,
        username: str,
        video_filename: str
    ) -> Dict[str, Any]:
        """Remove a like from the database."""
        cursor.execute(
            f"DELETE FROM {TABLE_LIKES} WHERE username=? AND video_filename=?",
            (username, video_filename)
        )
        conn.commit()
        return {
            "status": STATUS_SUCCESS,
            "message": MESSAGE_LIKE_REMOVED,
            "is_liked": False
        }

    def _add_like(
        self,
        conn,
        cursor,
        username: str,
        video_filename: str
    ) -> Dict[str, Any]:
        """Add a like to the database."""
        cursor.execute(
            f"INSERT INTO {TABLE_LIKES} (username, video_filename) "
            "VALUES (?, ?)",
            (username, video_filename),
        )
        conn.commit()
        return {
            "status": STATUS_SUCCESS,
            "message": MESSAGE_LIKE_ADDED,
            "is_liked": True
        }

    def get_likes_count(self, video_filename: str) -> int:
        """
        Get the number of likes for a video.

        Args:
            video_filename: Video filename

        Returns:
            Number of likes
        """
        result = self.execute_query(
            COUNT_LIKES_QUERY,
            (video_filename,),
            fetch_one=True
        )
        return result[SINGLE_RESULT_INDEX] if result else DEFAULT_LIKES_COUNT

    def add_story(
        self,
        username: str,
        content_type: str,
        content: str,
        filename: Optional[str],
        timestamp: str
    ) -> Dict[str, str]:
        """
        Add a new story.

        Args:
            username: Story creator
            content_type: Type of story (text/image/video)
            content: Story content
            filename: Optional filename for media stories
            timestamp: Story timestamp

        Returns:
            Dict with status and message
        """
        try:
            query = f'''
                INSERT INTO {TABLE_STORIES}
                (username, content_type, content, filename, timestamp)
                VALUES (?, ?, ?, ?, ?)
            '''
            self.execute_query(
                query,
                (username, content_type, content, filename, timestamp),
                fetch_all=False
            )
            return {
                "status": STATUS_SUCCESS,
                "message": MESSAGE_STORY_ADDED
            }
        except Exception as e:
            return {"status": STATUS_ERROR, "message": str(e)}

    def get_stories(self, cutoff_time: str) -> List[Dict[str, Any]]:
        """
        Get all stories created after cutoff time.

        Args:
            cutoff_time: Timestamp cutoff

        Returns:
            List of story dictionaries
        """
        query = f'''
            SELECT username, content_type, content, filename, timestamp
            FROM {TABLE_STORIES}
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        '''
        rows = self.execute_query(query, (cutoff_time,))

        if not rows:
            return []

        return [
            {
                "username": row[STORY_ROW_USERNAME],
                "content_type": row[STORY_ROW_CONTENT_TYPE],
                "content": row[STORY_ROW_CONTENT],
                "filename": row[STORY_ROW_FILENAME],
                "timestamp": row[STORY_ROW_TIMESTAMP]
            }
            for row in rows
        ]

    def delete_old_stories(self, cutoff_time: str) -> int:
        """
        Delete stories older than cutoff time.

        Args:
            cutoff_time: Timestamp cutoff

        Returns:
            Number of deleted stories
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"DELETE FROM {TABLE_STORIES} WHERE timestamp < ?",
                    (cutoff_time,)
                )
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"Error deleting old stories: {e}")
            return 0

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of table to check

        Returns:
            bool: True if table exists
        """
        query = '''
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        '''
        result = self.execute_query(query, (table_name,), fetch_one=True)
        return result is not None

    def get_table_info(self, table_name: str) -> List[Tuple]:
        """
        Get table schema information.

        Args:
            table_name: Name of table

        Returns:
            List of column information tuples
        """
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query) or []

# Global singleton instance
_db_manager_instance = None


def get_db_manager() -> DBManager:
    """
    Get the singleton DBManager instance.

    Returns:
        DBManager: The database manager instance
    """
    global _db_manager_instance
    if _db_manager_instance is None:
        _db_manager_instance = DBManager()
    return _db_manager_instance
