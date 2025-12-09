import wx
import wx.lib.scrolledpanel as scrolled


class InstagramFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='Instagram Clone', size=(450, 800))
        self.SetBackgroundColour('#FAFAFA')

        # Main panel
        main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header
        header = self.create_header(main_panel)
        main_sizer.Add(header, 0, wx.EXPAND)

        # Stories section
        stories = self.create_stories(main_panel)
        main_sizer.Add(stories, 0, wx.EXPAND | wx.TOP, 5)

        # Feed
        feed = self.create_feed(main_panel)
        main_sizer.Add(feed, 1, wx.EXPAND)

        # Bottom navigation
        nav = self.create_bottom_nav(main_panel)
        main_sizer.Add(nav, 0, wx.EXPAND)

        main_panel.SetSizer(main_sizer)
        self.Centre()

    def create_header(self, parent):
        header = wx.Panel(parent, size=(-1, 60))
        header.SetBackgroundColour('#FFFFFF')

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Logo
        logo = wx.StaticText(header, label='📷 Instagram')
        font = wx.Font(20, wx.FONTFAMILY_SCRIPT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        logo.SetFont(font)

        sizer.Add(logo, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 15)

        # Icons
        icons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        add_btn = wx.Button(header, label='➕', size=(40, 40))
        add_btn.SetBackgroundColour('#FFFFFF')

        like_btn = wx.Button(header, label='❤️', size=(40, 40))
        like_btn.SetBackgroundColour('#FFFFFF')

        msg_btn = wx.Button(header, label='✉️', size=(40, 40))
        msg_btn.SetBackgroundColour('#FFFFFF')

        icons_sizer.Add(add_btn, 0, wx.RIGHT, 5)
        icons_sizer.Add(like_btn, 0, wx.RIGHT, 5)
        icons_sizer.Add(msg_btn, 0, wx.RIGHT, 15)

        sizer.Add(icons_sizer, 0, wx.ALIGN_CENTER_VERTICAL)

        header.SetSizer(sizer)
        return header

    def create_stories(self, parent):
        stories_panel = wx.Panel(parent, size=(-1, 110))
        stories_panel.SetBackgroundColour('#FFFFFF')

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddSpacer(10)

        # Create story circles
        story_names = ['הסטורי שלך', 'user_1', 'user_2', 'user_3', 'user_4', 'user_5']

        for name in story_names:
            story_box = wx.BoxSizer(wx.VERTICAL)

            # Story circle
            circle = wx.Panel(stories_panel, size=(70, 70))
            if name == 'הסטורי שלך':
                circle.SetBackgroundColour('#E1E1E1')
            else:
                circle.SetBackgroundColour('#FD5949')

            # Username
            username = wx.StaticText(stories_panel, label=name)
            username.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

            story_box.Add(circle, 0, wx.ALIGN_CENTER)
            story_box.AddSpacer(5)
            story_box.Add(username, 0, wx.ALIGN_CENTER)

            sizer.Add(story_box, 0, wx.RIGHT, 10)

        stories_panel.SetSizer(sizer)
        return stories_panel

    def create_feed(self, parent):
        feed_panel = scrolled.ScrolledPanel(parent)
        feed_panel.SetBackgroundColour('#FAFAFA')
        feed_panel.SetupScrolling()

        sizer = wx.BoxSizer(wx.VERTICAL)

        # Create 5 posts
        for i in range(1, 6):
            post = self.create_post(feed_panel, f'משתמש_{i}', f'זה הפוסט מספר {i}')
            sizer.Add(post, 0, wx.EXPAND | wx.TOP, 10)

        feed_panel.SetSizer(sizer)
        return feed_panel

    def create_post(self, parent, username, caption):
        post_panel = wx.Panel(parent)
        post_panel.SetBackgroundColour('#FFFFFF')

        sizer = wx.BoxSizer(wx.VERTICAL)

        # Post header
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        profile_pic = wx.Panel(post_panel, size=(35, 35))
        profile_pic.SetBackgroundColour('#C7C7C7')

        user_text = wx.StaticText(post_panel, label=username)
        user_text.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

        header_sizer.Add(profile_pic, 0, wx.ALL, 10)
        header_sizer.Add(user_text, 0, wx.ALIGN_CENTER_VERTICAL)
        header_sizer.AddStretchSpacer()

        more_btn = wx.Button(post_panel, label='⋮', size=(30, 30))
        more_btn.SetBackgroundColour('#FFFFFF')
        header_sizer.Add(more_btn, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)

        sizer.Add(header_sizer, 0, wx.EXPAND)

        # Post image
        image_panel = wx.Panel(post_panel, size=(-1, 350))
        image_panel.SetBackgroundColour('#E8E8E8')
        sizer.Add(image_panel, 0, wx.EXPAND)

        # Action buttons
        actions_sizer = wx.BoxSizer(wx.HORIZONTAL)

        like_btn = wx.Button(post_panel, label='❤️', size=(40, 40))
        like_btn.SetBackgroundColour('#FFFFFF')

        comment_btn = wx.Button(post_panel, label='💬', size=(40, 40))
        comment_btn.SetBackgroundColour('#FFFFFF')

        share_btn = wx.Button(post_panel, label='✈️', size=(40, 40))
        share_btn.SetBackgroundColour('#FFFFFF')

        actions_sizer.Add(like_btn, 0, wx.ALL, 5)
        actions_sizer.Add(comment_btn, 0, wx.ALL, 5)
        actions_sizer.Add(share_btn, 0, wx.ALL, 5)
        actions_sizer.AddStretchSpacer()

        save_btn = wx.Button(post_panel, label='🔖', size=(40, 40))
        save_btn.SetBackgroundColour('#FFFFFF')
        actions_sizer.Add(save_btn, 0, wx.ALL, 5)

        sizer.Add(actions_sizer, 0, wx.EXPAND)

        # Likes and caption
        likes = wx.StaticText(post_panel, label='234 לייקים')
        likes.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(likes, 0, wx.LEFT | wx.TOP, 10)

        caption_text = wx.StaticText(post_panel, label=f'{username} {caption}')
        sizer.Add(caption_text, 0, wx.LEFT | wx.TOP, 10)

        time_text = wx.StaticText(post_panel, label='לפני 2 שעות')
        time_text.SetForegroundColour('#8E8E8E')
        time_text.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(time_text, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 10)

        post_panel.SetSizer(sizer)
        return post_panel

    def create_bottom_nav(self, parent):
        nav_panel = wx.Panel(parent, size=(-1, 60))
        nav_panel.SetBackgroundColour('#FFFFFF')

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        icons = ['🏠', '🔍', '➕', '❤️', '👤']

        for icon in icons:
            btn = wx.Button(nav_panel, label=icon, size=(70, 50))
            btn.SetBackgroundColour('#FFFFFF')
            btn.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            sizer.Add(btn, 1, wx.EXPAND)

        nav_panel.SetSizer(sizer)
        return nav_panel


if __name__ == '__main__':
    app = wx.App()
    frame = InstagramFrame()
    frame.Show()
    app.MainLoop()