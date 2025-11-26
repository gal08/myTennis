import wx
import wx.lib.scrolledpanel as scrolled


class InstagramFrame(wx.Frame):
    def __init__(self, stories_users=None, posts_data=None):
        super().__init__(parent=None, title='Instagram', size=(400, 800))
        self.SetBackgroundColour(wx.Colour(255, 255, 255))

        # Default data if not provided
        self.stories_users = stories_users or []
        self.posts_data = posts_data or []

        # Track likes and UI elements
        self.post_likes = {}
        self.post_panels = {}

        # Main panel
        main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header
        header = self.create_header(main_panel)
        main_sizer.Add(header, 0, wx.EXPAND | wx.ALL, 0)

        # Scrollable content
        self.scroll = scrolled.ScrolledPanel(main_panel)
        self.scroll.SetupScrolling()
        scroll_sizer = wx.BoxSizer(wx.VERTICAL)

        # Stories
        stories = self.create_stories(self.scroll)
        scroll_sizer.Add(stories, 0, wx.EXPAND | wx.ALL, 10)

        # Separator
        line1 = wx.StaticLine(self.scroll)
        scroll_sizer.Add(line1, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # Posts
        for i, post_data in enumerate(self.posts_data):
            post = self.create_post(self.scroll, post_data, i)
            scroll_sizer.Add(post, 0, wx.EXPAND | wx.ALL, 0)

            # Add separator between posts
            if i < len(self.posts_data) - 1:
                line = wx.StaticLine(self.scroll)
                scroll_sizer.Add(line, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 10)

        self.scroll.SetSizer(scroll_sizer)
        main_sizer.Add(self.scroll, 1, wx.EXPAND)

        # Bottom navigation
        bottom_nav = self.create_bottom_nav(main_panel)
        main_sizer.Add(bottom_nav, 0, wx.EXPAND | wx.ALL, 0)

        main_panel.SetSizer(main_sizer)
        self.Centre()
        self.Show()

    def create_header(self, parent):
        # Main header container
        main_header = wx.Panel(parent)
        main_header.SetBackgroundColour(wx.Colour(255, 255, 255))
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Time panel
        time_panel = wx.Panel(main_header)
        time_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        time_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Time
        time_text = wx.StaticText(time_panel, label="11:23")
        time_text.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        time_sizer.Add(time_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 15)

        time_sizer.AddStretchSpacer()

        # Signal/battery icons (simplified)
        icons_text = wx.StaticText(time_panel, label="📶 🔋")
        time_sizer.Add(icons_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 15)

        time_panel.SetSizer(time_sizer)
        time_panel.SetMinSize((-1, 50))
        main_sizer.Add(time_panel, 0, wx.EXPAND)

        # Instagram header panel
        insta_panel = wx.Panel(main_header)
        insta_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        insta_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Instagram logo
        logo = wx.StaticText(insta_panel, label="tennis Instagram")
        font = wx.Font(24, wx.FONTFAMILY_SCRIPT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        logo.SetFont(font)
        insta_sizer.Add(logo, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 15)

        # Right icons
        heart_btn = wx.Button(insta_panel, label="♡", size=(40, 40), style=wx.BORDER_NONE)
        heart_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        heart_btn.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        insta_sizer.Add(heart_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

        msg_btn = wx.Button(insta_panel, label="✉", size=(40, 40), style=wx.BORDER_NONE)
        msg_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        msg_btn.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        insta_sizer.Add(msg_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        insta_panel.SetSizer(insta_sizer)
        main_sizer.Add(insta_panel, 0, wx.EXPAND)

        main_header.SetSizer(main_sizer)
        return main_header

    def create_stories(self, parent):
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Your story with profile picture
        story = self.create_story_circle(panel, "Your story", wx.Colour(200, 200, 200), has_plus=True)
        sizer.Add(story, 0, wx.ALL, 5)

        # Dynamic user stories
        colors = [
            wx.Colour(255, 100, 150),
            wx.Colour(255, 150, 50),
            wx.Colour(255, 200, 50),
            wx.Colour(150, 100, 255)
        ]

        # Show all stories dynamically
        for i, username in enumerate(self.stories_users):
            color = colors[i % len(colors)]
            story = self.create_story_circle(panel, username, color)
            sizer.Add(story, 0, wx.ALL, 5)

        panel.SetSizer(sizer)
        return panel

    def create_story_circle(self, parent, name, ring_color, has_plus=False):
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Container for circle and plus button
        circle_container = wx.Panel(panel)
        circle_container.SetBackgroundColour(wx.Colour(255, 255, 255))
        circle_sizer = wx.BoxSizer(wx.VERTICAL)

        # Circle button (profile picture)
        btn = wx.Button(circle_container, label="", size=(70, 70), style=wx.BORDER_SIMPLE)
        btn.SetBackgroundColour(wx.Colour(240, 240, 240))
        btn.SetForegroundColour(ring_color)

        if has_plus:
            # Add plus button overlay for "Your story"
            overlay_sizer = wx.BoxSizer(wx.VERTICAL)
            overlay_sizer.Add(btn, 0, wx.ALIGN_CENTER)

            plus_btn = wx.Button(circle_container, label="+", size=(25, 25), style=wx.BORDER_SIMPLE)
            plus_btn.SetBackgroundColour(wx.Colour(0, 100, 255))
            plus_btn.SetForegroundColour(wx.Colour(255, 255, 255))
            plus_btn.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            overlay_sizer.Add(plus_btn, 0, wx.ALIGN_RIGHT | wx.TOP, -25)

            circle_sizer.Add(overlay_sizer, 0, wx.ALIGN_CENTER)
        else:
            circle_sizer.Add(btn, 0, wx.ALIGN_CENTER)

        circle_container.SetSizer(circle_sizer)
        sizer.Add(circle_container, 0, wx.ALIGN_CENTER)

        # Name
        text = wx.StaticText(panel, label=name)
        text.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(text, 0, wx.ALIGN_CENTER | wx.TOP, 5)

        panel.SetSizer(sizer)
        return panel

    def create_post(self, parent, post_data, post_id):
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Post header
        header_panel = wx.Panel(panel)
        header_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Profile pic with story ring
        profile_btn = wx.Button(header_panel, label="", size=(35, 35), style=wx.BORDER_SIMPLE)
        profile_btn.SetBackgroundColour(wx.Colour(220, 220, 220))
        profile_btn.SetForegroundColour(wx.Colour(255, 100, 150))
        header_sizer.Add(profile_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)

        # Username and music info container
        info_container = wx.BoxSizer(wx.VERTICAL)

        # Username
        username = wx.StaticText(header_panel, label=post_data['username'])
        username.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        info_container.Add(username, 0, wx.ALIGN_LEFT)

        # Music info if exists
        if post_data.get('music'):
            music = wx.StaticText(header_panel, label=f"♪ {post_data['music']}")
            music.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            music.SetForegroundColour(wx.Colour(100, 100, 100))
            info_container.Add(music, 0, wx.ALIGN_LEFT)

        header_sizer.Add(info_container, 1, wx.ALIGN_CENTER_VERTICAL)

        # More button
        more_btn = wx.Button(header_panel, label="⋯", style=wx.BORDER_NONE)
        more_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        more_btn.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        header_sizer.Add(more_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        header_panel.SetSizer(header_sizer)
        sizer.Add(header_panel, 0, wx.EXPAND)

        # Post image placeholder
        image_panel = wx.Panel(panel, size=(-1, 400))
        image_panel.SetBackgroundColour(wx.Colour(180, 180, 180))

        img_sizer = wx.BoxSizer(wx.VERTICAL)

        # Counter (1/2) in top right
        counter_panel = wx.Panel(image_panel)
        counter_panel.SetBackgroundColour(wx.Colour(80, 80, 80))
        counter_text = wx.StaticText(counter_panel, label="1/2")
        counter_text.SetForegroundColour(wx.Colour(255, 255, 255))
        counter_text.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        counter_sizer = wx.BoxSizer(wx.HORIZONTAL)
        counter_sizer.Add(counter_text, 0, wx.ALL, 5)
        counter_panel.SetSizer(counter_sizer)

        img_sizer.Add(counter_panel, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        img_sizer.AddStretchSpacer()

        # Caption overlay at bottom if exists
        if post_data.get('caption'):
            caption_panel = wx.Panel(image_panel)
            caption_panel.SetBackgroundColour(wx.Colour(255, 200, 200))
            caption_text = wx.StaticText(caption_panel, label=post_data['caption'])
            caption_text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            caption_text.SetForegroundColour(wx.Colour(200, 0, 0))
            caption_sizer = wx.BoxSizer(wx.HORIZONTAL)
            caption_sizer.Add(caption_text, 1, wx.ALL, 10)
            caption_panel.SetSizer(caption_sizer)
            img_sizer.Add(caption_panel, 0, wx.EXPAND | wx.ALL, 10)

        image_panel.SetSizer(img_sizer)
        sizer.Add(image_panel, 0, wx.EXPAND)

        # Action buttons (like, comment, share, save)
        actions_panel = wx.Panel(panel)
        actions_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        actions_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Like button
        like_btn = wx.Button(actions_panel, label="♡", size=(40, 40), style=wx.BORDER_NONE, name=f"like_{post_id}")
        like_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        like_btn.SetFont(wx.Font(22, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        like_btn.Bind(wx.EVT_BUTTON, lambda evt, pid=post_id: self.on_like(evt, pid))
        actions_sizer.Add(like_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)

        # Comment button
        comment_btn = wx.Button(actions_panel, label="💬", size=(40, 40), style=wx.BORDER_NONE,
                                name=f"comment_{post_id}")
        comment_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        comment_btn.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        comment_btn.Bind(wx.EVT_BUTTON, lambda evt, pid=post_id: self.on_comment(evt, pid))
        actions_sizer.Add(comment_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        # Share button
        share_btn = wx.Button(actions_panel, label="✈", size=(40, 40), style=wx.BORDER_NONE)
        share_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        share_btn.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        actions_sizer.Add(share_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        actions_sizer.AddStretchSpacer()

        # Save button
        save_btn = wx.Button(actions_panel, label="🔖", size=(40, 40), style=wx.BORDER_NONE)
        save_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        save_btn.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        actions_sizer.Add(save_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        actions_panel.SetSizer(actions_sizer)
        sizer.Add(actions_panel, 0, wx.EXPAND | wx.TOP, 5)

        # Likes count
        likes_count = post_data.get('likes', 0)
        likes_text = wx.StaticText(panel, label=f"{likes_count} likes", name=f"likes_text_{post_id}")
        likes_text.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(likes_text, 0, wx.LEFT | wx.TOP, 15)

        # Comments section
        if post_data.get('comments'):
            for comment in post_data['comments'][:3]:  # Show max 3 comments
                comment_panel = wx.Panel(panel)
                comment_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
                comment_sizer = wx.BoxSizer(wx.HORIZONTAL)

                comment_user = wx.StaticText(comment_panel, label=comment['username'])
                comment_user.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
                comment_sizer.Add(comment_user, 0, wx.ALIGN_CENTER_VERTICAL)

                comment_text = wx.StaticText(comment_panel, label=f"  {comment['text']}")
                comment_text.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
                comment_sizer.Add(comment_text, 1, wx.ALIGN_CENTER_VERTICAL)

                comment_panel.SetSizer(comment_sizer)
                sizer.Add(comment_panel, 0, wx.EXPAND | wx.LEFT | wx.TOP, 15)

        # Add comment input area
        add_comment_panel = wx.Panel(panel)
        add_comment_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        add_comment_sizer = wx.BoxSizer(wx.HORIZONTAL)

        comment_hint = wx.StaticText(add_comment_panel, label="Add a comment...")
        comment_hint.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        comment_hint.SetForegroundColour(wx.Colour(150, 150, 150))
        add_comment_sizer.Add(comment_hint, 1, wx.ALIGN_CENTER_VERTICAL)

        add_comment_panel.SetSizer(add_comment_sizer)
        sizer.Add(add_comment_panel, 0, wx.EXPAND | wx.ALL, 15)

        panel.SetSizer(sizer)
        return panel

    def on_like(self, event, post_id):
        btn = event.GetEventObject()

        # Toggle like
        if post_id not in self.post_likes:
            self.post_likes[post_id] = False

        self.post_likes[post_id] = not self.post_likes[post_id]

        # Update button appearance
        if self.post_likes[post_id]:
            btn.SetLabel("❤")
            btn.SetForegroundColour(wx.Colour(255, 0, 0))
            # Update likes count
            likes_text = self.scroll.FindWindowByName(f"likes_text_{post_id}")
            if likes_text:
                current_likes = self.posts_data[post_id].get('likes', 0)
                # Note: This is a local update, the original data is not changed
                likes_text.SetLabel(f"{current_likes + 1} likes")
        else:
            btn.SetLabel("♡")
            btn.SetForegroundColour(wx.Colour(0, 0, 0))
            # Update likes count
            likes_text = self.scroll.FindWindowByName(f"likes_text_{post_id}")
            if likes_text:
                current_likes = self.posts_data[post_id].get('likes', 0)
                likes_text.SetLabel(f"{current_likes} likes")

        self.scroll.Layout()
        self.scroll.Refresh()

    def on_comment(self, event, post_id):
        # Open comment dialog
        dlg = wx.TextEntryDialog(self, 'Enter your comment:', 'Add Comment')

        if dlg.ShowModal() == wx.ID_OK:
            comment_text = dlg.GetValue()
            if comment_text:
                # Add comment to post data
                new_comment = {'username': 'You', 'text': comment_text}
                if 'comments' not in self.posts_data[post_id]:
                    self.posts_data[post_id]['comments'] = []
                self.posts_data[post_id]['comments'].append(new_comment)

                # Refresh the posts display
                self.refresh_posts()

        dlg.Destroy()

    def refresh_posts(self):
        # Clear current posts
        scroll_sizer = self.scroll.GetSizer()

        # Remove all children after the Stories panel (index 0) and the separator line (index 1)
        # Iterate backwards to safely destroy windows
        children = scroll_sizer.GetChildren()
        for i in range(len(children) - 1, 1, -1):
            child = children[i]
            window = child.GetWindow()
            if window:
                scroll_sizer.Detach(window)
                window.Destroy()

        # Re-add all posts
        for i, post_data in enumerate(self.posts_data):
            post = self.create_post(self.scroll, post_data, i)
            scroll_sizer.Add(post, 0, wx.EXPAND | wx.ALL, 0)

            # Add separator between posts
            if i < len(self.posts_data) - 1:
                line = wx.StaticLine(self.scroll)
                scroll_sizer.Add(line, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 10)

        self.scroll.Layout()
        self.scroll.SetupScrolling()
        self.scroll.Refresh()

    def create_bottom_nav(self, parent):
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        icons = [
            ("🏠", wx.Colour(0, 0, 0)),
            ("🔍", wx.Colour(0, 0, 0)),
            ("➕", wx.Colour(0, 0, 0)),
            ("▶", wx.Colour(0, 0, 0)),
            ("👤", wx.Colour(0, 0, 0))
        ]

        for icon, color in icons:
            btn = wx.Button(panel, label=icon, style=wx.BORDER_NONE, size=(75, 50))
            btn.SetBackgroundColour(wx.Colour(255, 255, 255))
            btn.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            btn.SetForegroundColour(color)
            sizer.Add(btn, 1, wx.EXPAND)

        panel.SetSizer(sizer)
        return panel


if __name__ == '__main__':
    app = wx.App()

    # Dynamic Mock Data
    stories_users = ["user 1", "user 2", "user 3", "user 4", "user 5"]

    posts_data = [
        {
            'username': 'user 1',
            'likes': 150,
            'comments': [
                {'username': 'user 2', 'text': 'Awesome work!'},
                {'username': 'user 3', 'text': 'The UI looks fantastic 👏'}
            ]
        },
        {
            'username': 'user 4',
            'likes': 95,
            'comments': [
                {'username': 'user 1', 'text': 'Incredible shot!'},
            ]
        },
        {
            'username': 'user 6',
            'likes': 280,
            'comments': [
                {'username': 'user 1', 'text': 'Looks amazing, can\'t wait!'},
                {'username': 'user 2', 'text': 'Looks delicious!'},
                {'username': 'user 3', 'text': 'What spices did you use?'}
            ]
        }
    ]

    frame = InstagramFrame(stories_users=stories_users, posts_data=posts_data)
    app.MainLoop()