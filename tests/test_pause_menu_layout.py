"""Layout puro do menu de pausa, derivado do número de botões."""

import unittest

from src.config.layout import (
    PAUSE_BUTTON_FOOTER_GAP,
    PAUSE_BUTTON_GAP,
    PAUSE_BUTTON_HEIGHT,
    PAUSE_BUTTON_WIDTH,
    PAUSE_DIVIDER_BUTTON_GAP,
    PAUSE_EYEBROW_HEIGHT,
    PAUSE_FOOTER_HEIGHT,
    PAUSE_PANEL_BOTTOM_PADDING,
    PAUSE_PANEL_TOP_PADDING,
    PAUSE_PANEL_WIDTH,
    PAUSE_SUBTITLE_HEIGHT,
    PAUSE_TITLE_HEIGHT,
    PAUSE_TITLE_SUBTITLE_GAP,
    compute_pause_menu_layout,
)
from src.config.settings import HEIGHT, WIDTH


class PauseMenuLayoutTests(unittest.TestCase):
    def test_panel_is_centered_on_virtual_screen(self):
        for button_count in (2, 3, 4):
            with self.subTest(button_count=button_count):
                layout = compute_pause_menu_layout(button_count)
                x, y, width, height = layout.panel
                self.assertEqual(width, PAUSE_PANEL_WIDTH)
                self.assertEqual(x + width // 2, WIDTH // 2)
                self.assertEqual(y + height // 2, HEIGHT // 2)

    def test_buttons_keep_size_alignment_and_equal_spacing(self):
        layout = compute_pause_menu_layout(3)
        self.assertEqual(len(layout.buttons), 3)

        x_positions = {rect[0] for rect in layout.buttons}
        sizes = {(rect[2], rect[3]) for rect in layout.buttons}
        self.assertEqual(x_positions, {layout.buttons[0][0]})
        self.assertEqual(sizes, {(PAUSE_BUTTON_WIDTH, PAUSE_BUTTON_HEIGHT)})

        tops = [rect[1] for rect in layout.buttons]
        gaps = [following - current for current, following in zip(tops, tops[1:])]
        self.assertEqual(gaps, [PAUSE_BUTTON_HEIGHT + PAUSE_BUTTON_GAP] * 2)

        for current, following in zip(layout.buttons, layout.buttons[1:]):
            self.assertGreaterEqual(following[1], current[1] + current[3])

    def test_panel_contains_header_buttons_and_footer(self):
        layout = compute_pause_menu_layout(3)
        panel_x, panel_y, panel_width, panel_height = layout.panel
        panel_bottom = panel_y + panel_height

        self.assertGreaterEqual(
            layout.eyebrow_center_y - PAUSE_EYEBROW_HEIGHT // 2,
            panel_y + PAUSE_PANEL_TOP_PADDING,
        )

        for rect in layout.buttons:
            x, y, width, height = rect
            self.assertGreaterEqual(x, panel_x)
            self.assertLessEqual(x + width, panel_x + panel_width)
            self.assertGreaterEqual(y, panel_y)
            self.assertLessEqual(y + height, panel_bottom)

        last_button_bottom = layout.buttons[-1][1] + layout.buttons[-1][3]
        footer_top = layout.footer_center_y - PAUSE_FOOTER_HEIGHT // 2
        footer_bottom = layout.footer_center_y + PAUSE_FOOTER_HEIGHT // 2

        self.assertGreaterEqual(footer_top - last_button_bottom, PAUSE_BUTTON_FOOTER_GAP)
        self.assertGreaterEqual(
            panel_bottom - footer_bottom, PAUSE_PANEL_BOTTOM_PADDING
        )
        self.assertLessEqual(
            panel_bottom - footer_bottom, PAUSE_PANEL_BOTTOM_PADDING + 1
        )

    def test_subtitle_and_divider_respect_header_spacing(self):
        layout = compute_pause_menu_layout(3)
        panel_x, _, panel_width, _ = layout.panel

        title_bottom = layout.title_center_y + PAUSE_TITLE_HEIGHT // 2
        subtitle_top = layout.subtitle_center_y - PAUSE_SUBTITLE_HEIGHT // 2
        subtitle_bottom = layout.subtitle_center_y + PAUSE_SUBTITLE_HEIGHT // 2
        first_button_top = layout.buttons[0][1]

        self.assertGreaterEqual(
            subtitle_top - title_bottom, PAUSE_TITLE_SUBTITLE_GAP
        )
        self.assertGreaterEqual(
            first_button_top - subtitle_bottom, PAUSE_BUTTON_HEIGHT // 2
        )

        self.assertGreater(layout.divider_y, subtitle_bottom)
        self.assertLess(layout.divider_y, first_button_top)
        self.assertGreaterEqual(
            first_button_top - layout.divider_y, PAUSE_DIVIDER_BUTTON_GAP
        )
        self.assertEqual(
            (layout.divider_x1 + layout.divider_x2) // 2,
            panel_x + panel_width // 2,
        )

    def test_height_grows_by_one_button_row_each_step(self):
        layouts = {
            count: compute_pause_menu_layout(count) for count in (2, 3, 4)
        }
        expected_step = PAUSE_BUTTON_HEIGHT + PAUSE_BUTTON_GAP

        self.assertEqual(
            layouts[3].panel[3] - layouts[2].panel[3], expected_step
        )
        self.assertEqual(
            layouts[4].panel[3] - layouts[3].panel[3], expected_step
        )
        for layout in layouts.values():
            x, y, width, height = layout.panel
            self.assertEqual(x + width // 2, WIDTH // 2)
            self.assertEqual(y + height // 2, HEIGHT // 2)

    def test_requires_at_least_one_button(self):
        with self.assertRaises(ValueError):
            compute_pause_menu_layout(0)


if __name__ == "__main__":
    unittest.main()
