"""
Gal Haham
Entry point for displaying all videos in a grid.
Provides the run() function to launch the videos display window.
REFACTORED: Main classes separated into individual files.
"""
from Allvideosframe import AllVideosFrame


def run(client_ref, parent_menu=None):
    """
    Create and show the all videos frame.

    This is the main entry point for displaying the videos grid.
    It creates an AllVideosFrame window with a VideoGridPanel inside.

    Args:
        client_ref: Client instance for server communication
        parent_menu: Parent menu frame (optional) - will
         be shown when window closes

    Returns:
        AllVideosFrame: Created frame instance
    """
    frame = AllVideosFrame(client_ref, parent_menu=parent_menu)
    return frame
