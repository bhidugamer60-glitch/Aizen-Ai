# aizen_kv.py  -  PART 1b: the KV layout text
KV = """
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp

<Pill>:
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    color: 0.91, 0.93, 0.97, 1
    font_size: sp(13)

    canvas.before:
        Color:
            rgba: self.fill_down if self.state == 'down' else self.fill
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.height / 2.0]


<Bubble>:
    orientation: 'horizontal'
    size_hint_y: None
    height: card.height + dp(4)
    padding: dp(16), dp(2)

    Widget:
        size_hint_x: 1 if root.mine else None
        width: 0

    BoxLayout:
        id: card
        size_hint: None, None
        size: msg.width + dp(28), msg.height + dp(22)
        padding: dp(14), dp(11)

        canvas.before:
            Color:
                rgba: (0.30, 0.55, 1.0, 1) if root.mine else (0.11, 0.15, 0.28, 1)
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(18), dp(18), dp(4), dp(18)] if root.mine else [dp(18), dp(18), dp(18), dp(4)]

        Label:
            id: msg
            text: root.text
            font_size: sp(15)
            color: (1, 1, 1, 1) if root.mine else (0.91, 0.93, 0.97, 1)
            halign: 'left'
            valign: 'top'
            size_hint: None, None
            text_size: root.width * 0.74, None
            size: self.texture_size

    Widget:
        size_hint_x: None if root.mine else 1
        width: 0


<Root>:
    orientation: 'vertical'

    canvas.before:
        Color:
            rgba: 0.043, 0.063, 0.125, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint_y: None
        height: dp(64)
        padding: dp(20), dp(8)
        spacing: dp(8)

        BoxLayout:
            orientation: 'vertical'

            Label:
                text: 'Aizen'
                bold: True
                font_size: sp(22)
                color: 0.91, 0.93, 0.97, 1
                halign: 'left'
                valign: 'bottom'
                text_size: self.size

            Label:
                text: root.subtitle
                font_size: sp(12)
                color: 0.54, 0.58, 0.70, 1
                halign: 'left'
                valign: 'top'
                text_size: self.size

        AnchorLayout:
            size_hint_x: None
            width: dp(112)
            anchor_x: 'right'
            anchor_y: 'center'

            BoxLayout:
                size_hint: None, None
                size: dp(104), dp(32)
                padding: dp(12), 0
                spacing: dp(8)

                canvas.before:
                    Color:
                        rgba: 0.09, 0.13, 0.25, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(16)]

                AnchorLayout:
                    size_hint_x: None
                    width: dp(8)

                    Widget:
                        size_hint: None, None
                        size: dp(8), dp(8)

                        canvas:
                            Color:
                                rgba: root.status_color
                            Ellipse:
                                pos: self.pos
                                size: self.size

                Label:
                    text: root.status
                    font_size: sp(12)
                    color: 0.91, 0.93, 0.97, 1
                    halign: 'left'
                    valign: 'middle'
                    text_size: self.size

    FloatLayout:
        size_hint_y: None
        height: root.orb_h

        Orb:
            id: orb
            size_hint: None, None
            size: root.orb_h - dp(16), root.orb_h - dp(16)
            pos_hint: {'center_x': .5, 'center_y': .5}

        Label:
            text: root.orb_label
            size_hint: None, None
            size: dp(180), dp(28)
            pos_hint: {'center_x': .5, 'y': .03}
            color: 0.65, 0.72, 0.90, 1
            font_size: sp(12)
            halign: 'center'
            text_size: self.size

    ScrollView:
        size_hint_y: None
        height: dp(50)
        do_scroll_y: False
        bar_width: 0

        BoxLayout:
            size_hint_x: None
            width: self.minimum_width
            padding: dp(20), dp(7)
            spacing: dp(8)

            Pill:
                text: 'Search the web'
                size_hint_x: None
                width: self.texture_size[0] + dp(32)
                on_release: root.use_prompt('Search the web for ')

            Pill:
                text: 'Help me edit'
                size_hint_x: None
                width: self.texture_size[0] + dp(32)
                on_release: root.use_prompt('Help me edit a video: ')

            Pill:
                text: 'Write something'
                size_hint_x: None
                width: self.texture_size[0] + dp(32)
                on_release: root.use_prompt('Write ')

            Pill:
                text: 'Explain'
                size_hint_x: None
                width: self.texture_size[0] + dp(32)
                on_release: root.use_prompt('Explain ')

    ScrollView:
        id: scroll
        do_scroll_x: False
        bar_width: dp(3)
        bar_color: 0.30, 0.55, 1, 0.5

        BoxLayout:
            id: chat
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            padding: 0, dp(8)
            spacing: dp(4)

    BoxLayout:
        size_hint_y: None
        height: dp(72)
        padding: dp(14), dp(12)
        spacing: dp(8)

        TextInput:
            id: inp
            hint_text: 'Message Aizen'
            multiline: False
            write_tab: False
            font_size: sp(15)
            background_normal: ''
            background_active: ''
            background_color: 0, 0, 0, 0
            foreground_color: 0.91, 0.93, 0.97, 1
            hint_text_color: 0.45, 0.50, 0.65, 1
            cursor_color: 0.30, 0.55, 1, 1
            padding: [dp(18), (self.height - self.line_height) / 2.0, dp(18), 0]
            on_text_validate: root.send()

            canvas.before:
                Color:
                    rgba: 0.09, 0.13, 0.25, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(24)]

        Pill:
            text: 'Call'
            size_hint_x: None
            width: dp(58)
            fill: 0.12, 0.34, 0.29, 1
            fill_down: 0.10, 0.27, 0.23, 1
            on_release: root.toggle_call()

        Pill:
            text: 'Send'
            bold: True
            size_hint_x: None
            width: dp(68)
            fill: 0.30, 0.55, 1, 1
            fill_down: 0.22, 0.43, 0.85, 1
            color: 1, 1, 1, 1
            on_release: root.send()
"""
