"""
Gal Haham
Video & audio streaming client - Main Entry Point
This is the main file that should be run or imported
"""
import wx
from Video_Audio_Client_Frame import VideoAudioClientFrame


def run_video_player_client():
    """
    Run the video player client.
    Properly handles wx.App creation and cleanup.
    """
    # Check if there's already a wx.App running
    app = wx.App.Get()

    if app is None:
        # No app exists, create a new one
        app = wx.App()
        frame = VideoAudioClientFrame()
        app.MainLoop()
    else:
        # App already exists (called from within another wx app)
        # Just create the frame
        frame = VideoAudioClientFrame()
        # Don't call MainLoop again - it's already running



if __name__ == '__main__':
    run_video_player_client()
