import unittest
from unittest.mock import MagicMock, call, patch

import pygame
from src.core import scene_manager
from src.scenes.save_selection_scene import SaveSelectionScene
from src.scenes.shop_scene import ShopScene
from src.systems import save_manager
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

    def test_delete_confirmation_plays_sound_once(self):
        scene_manager = MagicMock()
        save_manager = MagicMock()

        scene = SaveSelectionScene(
            scene_manager,
            MagicMock(),
            MagicMock(),
            save_manager,
        )

        scene._request_delete(0)

        modal = scene_manager.push_modal.call_args.args[0]
        modal._confirm()

        self.assertEqual(
            scene_manager.audio_manager.play_sfx.call_args_list,
            [
                call("ui.click", volume=1.0),
                call("ui.confirm", volume=1.0),
            ],
        )

        save_manager.delete_save.assert_called_once()

    def test_open_test_save_plays_confirm_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        save_manager = MagicMock()

        scene = SaveSelectionScene(
            scene_manager,
            window_manager,
            MagicMock(),
            save_manager,
        )

        with patch("src.scenes.map_scene.MapScene"):
            scene._open_test_save()

        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.confirm",
            volume=1.0,
        )

    def test_fullscreen_button_plays_click_sound(self):
        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        scene = SaveSelectionScene(
            scene_manager,
            window_manager,
            MagicMock(),
            MagicMock(),
        )

        window_manager.map_to_virtual.return_value = (10, 10)
        window_manager.get_fullscreen_button_rect.return_value.collidepoint.return_value = True

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"button": 1, "pos": (10, 10)},
        )

        scene.handle_event(event)

        window_manager.toggle_fullscreen.assert_called_once()
        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )

    def test_open_delete_confirmation_plays_click_sound(self):
        scene_manager = MagicMock()

        scene = SaveSelectionScene(
            scene_manager,
            MagicMock(),
            MagicMock(),
            MagicMock(),
        )

        scene._request_delete(0)

        scene_manager.push_modal.assert_called_once()
        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )


class TestConfirmationModalAudio(unittest.TestCase):
    def test_confirm_plays_confirm_sound(self):
        from src.scenes.confirmation_modal import ConfirmationModal

        scene_manager = MagicMock()
        on_confirm = MagicMock()

        modal = ConfirmationModal(
            scene_manager,
            MagicMock(),
            MagicMock(),
            on_confirm=on_confirm,
        )

        modal._confirm()

        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.confirm",
            volume=1.0,
        )
        scene_manager.pop_modal.assert_called_once()
        on_confirm.assert_called_once()


class TestBattleMenuAudio(unittest.TestCase):
    def test_open_menu_confirmation_plays_click_sound(self):
        from src.scenes.battle_scene import BattleScene

        scene_manager = MagicMock()

        scene = object.__new__(BattleScene)
        scene.scene_manager = scene_manager
        scene.window_manager = MagicMock()
        scene.asset_manager = MagicMock()
        scene.engine = MagicMock()
        scene.engine.state = "player_turn"

        scene._open_menu_confirmation()

        scene_manager.push_modal.assert_called_once()
        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )


class TestTutorialReopenAudio(unittest.TestCase):
    def test_reopen_guide_plays_click_sound(self):
        from src.scenes.tutorial_scene import TutorialScene

        events = {
            "button": pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {"button": 1, "pos": (10, 10)},
            ),
            "H": pygame.event.Event(
                pygame.KEYDOWN,
                {"key": pygame.K_h},
            ),
            "F1": pygame.event.Event(
                pygame.KEYDOWN,
                {"key": pygame.K_F1},
            ),
        }

        for interaction, event in events.items():
            with self.subTest(interaction=interaction):
                scene_manager = MagicMock()
                window_manager = MagicMock()
                window_manager.map_to_virtual.return_value = (10, 10)

                scene = object.__new__(TutorialScene)
                scene.scene_manager = scene_manager
                scene.window_manager = window_manager
                scene.asset_manager = MagicMock()
                scene.engine = MagicMock()
                scene.engine.state = "player_turn"
                scene.overlay = MagicMock()
                scene.overlay.is_active = False
                scene.help_button_rect = pygame.Rect(0, 0, 20, 20)

                scene.handle_event(event)

                scene.overlay.reset.assert_called_once()
                scene_manager.audio_manager.play_sfx.assert_called_once_with(
                    "ui.click",
                    volume=1.0,
                )


class TestShopEscapeAudio(unittest.TestCase):
    def test_escape_plays_click_sound(self):
        from src.scenes.shop_scene import ShopScene

        scene_manager = MagicMock()
        window_manager = MagicMock()
        window_manager.handle_window_event.return_value = False

        scene = object.__new__(ShopScene)
        scene.scene_manager = scene_manager
        scene.window_manager = window_manager
        scene._back = MagicMock()

        event = pygame.event.Event(
            pygame.KEYDOWN,
            {"key": pygame.K_ESCAPE},
        )

        scene.handle_event(event)

        scene._back.assert_called_once()
        scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )


class TestShopPurchaseAudio(unittest.TestCase):
    def test_purchase_feedback_plays_correct_sound(self):
        from src.scenes.shop_scene import ShopScene

        cases = (
            (True, "ui.confirm"),
            (False, "ui.click"),
        )

        for success, expected_sound in cases:
            with self.subTest(success=success):
                scene_manager = MagicMock()

                scene = object.__new__(ShopScene)
                scene.scene_manager = scene_manager

                result = MagicMock()
                result.success = success
                result.message = "Resultado da compra"

                scene._notify(result)

                self.assertEqual(scene.message, result.message)
                self.assertEqual(scene.message_positive, success)
                self.assertEqual(scene.message_timer, 3600)

                scene_manager.audio_manager.play_sfx.assert_called_once_with(
                    expected_sound,
                    volume=1.0,
                )


class TestF11Audio(unittest.TestCase):
    def test_f11_plays_click_sound_once(self):
        import pygame
        from src.core.scene_manager import SceneManager

        audio_manager = MagicMock()
        scene_manager = SceneManager(audio_manager=audio_manager)

        scene = MagicMock()
        scene_manager.change_scene(scene)

        event = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_F11,
        )

        scene_manager.handle_event(event)

        audio_manager.play_sfx.assert_called_once_with(
            "ui.click",
            volume=1.0,
        )

        scene.handle_event.assert_called_once_with(event)


class TestMenuExitAudio(unittest.TestCase):
    def test_exit_plays_click_before_quitting(self):
        import pygame
        from unittest.mock import patch
        from src.scenes.menu_scene import MenuScene

        for exit_method in ("mouse", "escape"):
            with self.subTest(exit_method=exit_method):
                scene = object.__new__(MenuScene)
                scene.scene_manager = MagicMock()
                scene.window_manager = MagicMock()

                scene.window_manager.handle_window_event.return_value = False
                scene.window_manager.map_to_virtual.return_value = (50, 50)
                scene.window_manager.get_fullscreen_button_rect.return_value = (
                    pygame.Rect(200, 200, 50, 50)
                )

                scene.play_button = pygame.Rect(300, 300, 50, 50)
                scene.quit_button = pygame.Rect(0, 0, 100, 100)

                if exit_method == "mouse":
                    event = pygame.event.Event(
                        pygame.MOUSEBUTTONDOWN,
                        button=1,
                        pos=(50, 50),
                    )
                else:
                    event = pygame.event.Event(
                        pygame.KEYDOWN,
                        key=pygame.K_ESCAPE,
                    )

                with patch("src.scenes.menu_scene.pygame.quit") as mock_quit:
                    with patch("src.scenes.menu_scene.sys.exit") as mock_exit:
                        scene.handle_event(event)

                mock_quit.assert_called_once_with()
                mock_exit.assert_called_once_with()

                scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(
                    "ui.click",
                    volume=1.0,
                )


if __name__ == "__main__":
    unittest.main()
