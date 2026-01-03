"""
Gal Haham
Entry point for displaying all stories in a grid.
Provides the run() function to launch the stories display window.
REFACTORED: Main classes separated into individual files.
"""
from Allstoriesframe import AllStoriesFrame


def run(client_ref, parent_menu=None):
    """
    Create and show the all stories frame.

    This is the main entry point for displaying the stories grid.
    It creates an AllStoriesFrame window with a StoryGridPanel inside.

    Args:
        client_ref: Client instance for server communication
        parent_menu: Parent menu frame (optional) -
        will be shown when window closes

    Returns:
        AllStoriesFrame: Created frame instance
    """
    frame = AllStoriesFrame(client_ref, parent_menu=parent_menu)
    return frame
