import unittest
from unittest.mock import MagicMock, patch

import pygame
from src.scenes.save_selection_scene import SaveSelectionScene
from src.scenes.shop_scene import ShopScene
from src.systems.save_manager import SaveManager
from src.scenes.backpack_scene import BackpackScene


class TestShopAudio(unittest.TestCase):
    def test_previous_page_plays_click_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = ShopScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        scene._set_page(1)

        window_manager.map_to_virtual.return_value = scene.previous_page_rect.center

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=scene.previous_page_rect.center,
        )

        scene.handle_event(event)

        self.assertEqual(scene.page, 0)
        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )

    def test_next_page_plays_click_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = ShopScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        window_manager.map_to_virtual.return_value = scene.next_page_rect.center

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=scene.next_page_rect.center,
        )

        scene.handle_event(event)

        self.assertEqual(scene.page, 1)
        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )

    def test_back_to_map_plays_click_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = ShopScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        window_manager.map_to_virtual.return_value = scene.back_button.center

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=scene.back_button.center,
        )

        scene._back = MagicMock()

        scene.handle_event(event)

        scene._back.assert_called_once()
        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )


class TestBackpackAudio(unittest.TestCase):
    def test_select_card_plays_click_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        self.assertTrue(scene.cards)

        card_name, card_rect = next(iter(scene.cards.items()))

        window_manager.map_to_virtual.return_value = card_rect.center

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=card_rect.center,
        )

        scene.handle_event(event)

        self.assertEqual(scene.selected_card, card_name)
        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )

    def test_ultimate_tab_plays_click_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        self.assertEqual(scene.tab, "deck")

        window_manager.map_to_virtual.return_value = scene.ultimate_tab_rect.center

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=scene.ultimate_tab_rect.center,
        )

        scene.handle_event(event)

        self.assertEqual(scene.tab, "ultimates")
        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )

    def test_deck_tab_plays_click_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        scene.tab = "ultimates"

        window_manager.map_to_virtual.return_value = scene.deck_tab_rect.center

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=scene.deck_tab_rect.center,
        )

        scene.handle_event(event)

        self.assertEqual(scene.tab, "deck")
        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )

    def test_back_to_map_plays_click_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        window_manager.map_to_virtual.return_value = scene.back_rect.center

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=scene.back_rect.center,
        )

        scene._back = MagicMock()

        scene.handle_event(event)

        scene._back.assert_called_once()
        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )

    def test_next_page_plays_click_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        self.assertGreater(scene.page_count, 1)

        window_manager.map_to_virtual.return_value = scene.next_page_rect.center

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=scene.next_page_rect.center,
        )

        scene.handle_event(event)

        self.assertEqual(scene.page, 1)
        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )

    def test_previous_page_plays_click_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        scene._set_page(1)

        window_manager.map_to_virtual.return_value = scene.previous_page_rect.center

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=scene.previous_page_rect.center,
        )

        scene.handle_event(event)

        self.assertEqual(scene.page, 0)
        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )

    def test_select_deck_slot_plays_click_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        slot_index = 1
        slot_rect = scene.slots[slot_index]

        window_manager.map_to_virtual.return_value = slot_rect.center

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=slot_rect.center,
        )

        scene.handle_event(event)

        self.assertEqual(scene.selected_slot, slot_index)
        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )

    def test_equip_card_success_plays_confirm_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        card_name = save_data["progresso"]["cartas_colecao"][0]
        scene.selected_slot = 0

        with patch(
            "src.scenes.backpack_scene.equip_card_type",
            return_value=(True, "Deck atualizado."),
        ):
            scene._equip(card_name)

        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.confirm",
            volume=1.0,
        )

    def test_equip_card_failure_does_not_play_confirm_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        with patch(
            "src.scenes.backpack_scene.equip_card_type",
            return_value=(False, "Carta já equipada em outro espaço."),
        ):
            scene._equip("Carta de teste")

        scene_manager.audio_manager.play_sfx.assert_not_called()

    def test_clear_slot_success_plays_confirm_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        window_manager.map_to_virtual.return_value = scene.clear_rect.center

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=scene.clear_rect.center,
        )

        with patch(
            "src.scenes.backpack_scene.equip_card_type",
            return_value=(True, "Espaço esvaziado."),
        ) as mock_equip:
            scene.handle_event(event)

        mock_equip.assert_called_once_with(
            save_manager,
            save_data,
            scene.selected_slot,
            None,
        )

        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.confirm",
            volume=1.0,
        )

    def test_filter_button_plays_click_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        initial_filter = scene.owned_only

        window_manager.map_to_virtual.return_value = scene.filter_rect.center

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=scene.filter_rect.center,
        )

        scene.handle_event(event)

        self.assertNotEqual(scene.owned_only, initial_filter)

        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )

    def test_equip_ultimate_success_plays_confirm_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        scene.tab = "ultimates"

        equipped_id = save_data["progresso"].get("ultimate_equipada")
        available_ids = [uid for uid in scene.ultimate_buttons if uid != equipped_id]

        self.assertTrue(available_ids)
        target_id = available_ids[0]
        target_rect = scene.ultimate_buttons[target_id]

        window_manager.map_to_virtual.return_value = target_rect.center

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=target_rect.center,
        )

        with patch(
            "src.scenes.backpack_scene.equip_ultimate",
            return_value=(True, "Ultimate equipada."),
        ) as mock_equip:
            scene.handle_event(event)

        mock_equip.assert_called_once_with(
            save_manager,
            save_data,
            target_id,
        )

        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.confirm",
            volume=1.0,
        )

    def test_equip_ultimate_failure_does_not_play_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        scene.tab = "ultimates"

        equipped_id = save_data["progresso"].get("ultimate_equipada")
        available_ids = [uid for uid in scene.ultimate_buttons if uid != equipped_id]

        self.assertTrue(available_ids)

        target_id = available_ids[0]
        target_rect = scene.ultimate_buttons[target_id]

        window_manager.map_to_virtual.return_value = target_rect.center

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=target_rect.center,
        )

        with patch(
            "src.scenes.backpack_scene.equip_ultimate",
            return_value=(False, "Não foi possível equipar a Ultimate."),
        ) as mock_equip:
            scene.handle_event(event)

        mock_equip.assert_called_once_with(
            save_manager,
            save_data,
            target_id,
        )

        scene_manager.audio_manager.play_sfx.assert_not_called()

    def test_tab_key_plays_click_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        scene.tab = "deck"

        event = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_TAB,
        )

        scene.handle_event(event)

        self.assertEqual(scene.tab, "ultimates")

        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )

    def test_escape_key_plays_click_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        scene._back = MagicMock()

        event = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_ESCAPE,
        )

        scene.handle_event(event)

        scene._back.assert_called_once()

        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )

    def test_number_key_selects_slot_and_plays_click_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        scene.tab = "deck"
        scene.selected_slot = 0

        event = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_2,
        )

        scene.handle_event(event)

        self.assertEqual(scene.selected_slot, 1)

        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )

    def test_right_arrow_plays_click_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        scene.tab = "deck"
        scene.page = 0
        scene.page_count = 2

        event = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_RIGHT,
        )

        scene.handle_event(event)

        self.assertEqual(scene.page, 1)

        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )

    def test_left_arrow_plays_click_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        scene.tab = "deck"
        scene.page = 1
        scene.page_count = 2

        event = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_LEFT,
        )

        scene.handle_event(event)

        self.assertEqual(scene.page, 0)

        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )

    def test_enter_key_equips_card_and_plays_confirm_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        scene.tab = "deck"
        scene.selected_slot = 0
        scene.selected_card = save_data["progresso"]["cartas_colecao"][0]

        event = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_RETURN,
        )

        with patch(
            "src.scenes.backpack_scene.equip_card_type",
            return_value=(True, "Deck atualizado."),
        ) as mock_equip:
            scene.handle_event(event)

        mock_equip.assert_called_once_with(
            save_manager,
            save_data,
            0,
            scene.selected_card,
        )

        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.confirm",
            volume=1.0,
        )

    def test_mouse_wheel_page_change_plays_click_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        scene.tab = "deck"
        scene.owned_only = False
        scene._set_page(0)

        self.assertGreater(scene.page_count, 1)

        event = pygame.event.Event(
            pygame.MOUSEWHEEL,
            x=0,
            y=-1,
        )

        scene.handle_event(event)

        self.assertEqual(scene.page, 1)

        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )

    def test_mouse_wheel_at_first_page_does_not_play_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        save_manager = MagicMock()
        save_data = SaveManager()._new_data("Teste", "test")

        scene = BackpackScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
            save_data,
        )

        scene.tab = "deck"
        scene._set_page(0)

        event = pygame.event.Event(
            pygame.MOUSEWHEEL,
            x=0,
            y=1,
        )

        scene.handle_event(event)

        self.assertEqual(scene.page, 0)

        scene_manager.audio_manager.play_sfx.assert_not_called()


class TestSaveSelectionAudio(unittest.TestCase):
    def test_back_to_menu_plays_navigate_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        save_manager = MagicMock()

        scene = SaveSelectionScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
        )

        scene._back()

        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.navigate",
            volume=1.0,
        )
        scene_manager.change_scene.assert_called_once()


if __name__ == "__main__":
    unittest.main()
