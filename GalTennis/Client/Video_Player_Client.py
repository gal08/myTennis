"""
Gal Haham
Video & audio streaming client - Main Entry Point
This is the main file that should be run or imported
"""
import wx
from Video_Audio_Client_Frame import VideoAudioClientFrame


def run_video_player_client():
    """
    Main entry point for the video player client.
    Creates the wx application and shows the GUI frame.
    """
    app = wx.App()
    VideoAudioClientFrame()
    app.MainLoop()


if __name__ == '__main__':
    run_video_player_client()
