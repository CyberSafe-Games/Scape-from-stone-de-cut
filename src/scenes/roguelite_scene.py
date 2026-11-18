"""Preparação entre runs e oficina de cópias da loja, operáveis com mouse."""
import pygame

from src.scenes.base_scene import BaseScene
from src.config.colors import WHITE, GOLD, GRAY
from src.ui import dark_fantasy_theme as theme
from src.ui.helpers import draw_text, wrap_text
from src.systems.roguelite import (
    PREPARATION, MATERIAL_PRICE, UPGRADE_PRICES, instance_card, purchase_material,
    upgrade_copy, purchase_permanent, transact,
)


class RogueliteScene(BaseScene):
    """Uma tela compartilhada, mantendo compras de ouro e fragmentos separadas."""
    def __init__(self, scene_manager, window_manager, asset_manager, save_manager, save_data,
                 preparation=False):
        super().__init__(scene_manager, window_manager, asset_manager)
        self.save_manager, self.save_data = save_manager, save_data
        self.preparation = preparation
        self.page = 0
        self.message = ''
        self.buttons = []

    def update(self, dt):
        pass

    def _button(self, surface, rect, label, action, enabled=True):
        rect = pygame.Rect(rect)
        theme.button(surface, rect, label, self.asset_manager.small_font,
                     hover=rect.collidepoint(self.window_manager.get_virtual_mouse_pos()),
                     enabled=enabled)
        self.buttons.append((rect, action, enabled))

    def _notify(self, result):
        ok, self.message = result
        self.play_ui_sound('ui.confirm' if ok else 'ui.click')

    def draw(self, surface):
        self.buttons = []
        theme.backdrop(surface, self.asset_manager.background, opacity=235)
        a, p = self.asset_manager, self.save_data['progresso']
        profile = self.save_data['perfil']
        title = 'PREPARAÇÃO DA PRÓXIMA RUN' if self.preparation else 'OFICINA DE EVOLUÇÕES'
        draw_text(surface, title, a.big_font, WHITE, 80, 45)
        balance = f"FRAGMENTOS PERMANENTES: {profile['fragmentos']}" if self.preparation else (
            f"OURO DA RUN: {p['moedas']}    EVOLUÇÕES: {p['upgrades_purchased']}/3")
        draw_text(surface, balance, a.font, GOLD, 80, 125)
        if self.preparation:
            reason = 'Você concluiu a campanha!' if p['estado'] == 'concluida' else 'A run terminou.'
            draw_text(surface, reason + ' Seu perfil foi preservado neste slot.', a.font, WHITE, 80, 185)
            rows = [('vida', f"Vida permanente: +{profile['vida'] * 5} (máximo +15)", (3, 5, 8)),
                    ('energia', f"Energia inicial: {2 + profile['energia']} (máximo 3)", (12,)),
                    ('preparacao', f"Opções de cartas iniciais: nível {profile['preparacao']}/2", (4, 6))]
            for i, (kind, label, prices) in enumerate(rows):
                y = 260 + i * 130
                draw_text(surface, label, a.menu_font, WHITE, 100, y)
                level = profile[kind]
                price = prices[level] if level < len(prices) else None
                self._button(surface, (1200, y - 5, 580, 65),
                    f'COMPRAR · {price} FRAGMENTOS' if price else 'LIMITE ATINGIDO',
                    lambda k=kind: self._notify(purchase_permanent(self.save_manager, self.save_data, k)),
                    price is not None and profile['fragmentos'] >= price)
            draw_text(surface, 'Escolha um tipo extra LV1 para a nova run (não ocupa espaço automaticamente).',
                      a.small_font, GRAY, 100, 660)
            choices = PREPARATION[:3 if profile['preparacao'] == 1 else 6] if profile['preparacao'] else ()
            for i, name in enumerate(choices):
                label = ('✓ ' if profile.get('preparada') == name else '') + name
                self._button(surface, (100 + (i % 3) * 570, 710 + (i // 3) * 80, 540, 65), label,
                             lambda n=name: self._choose_preparation(n))
            self._button(surface, (1140, 930, 650, 70), 'INICIAR NOVA RUN · VIDA CHEIA', self._new_run)
        else:
            draw_text(surface, 'Três materiais do mesmo tipo + ouro evoluem somente a cópia escolhida.',
                      a.font, WHITE, 80, 185)
            names = [n for n in p['cartas_colecao'] if n in UPGRADE_PRICES]
            page_count = max(1, (len(names) + 3) // 4)
            self.page = max(0, min(self.page, page_count - 1))
            for i, name in enumerate(names[self.page * 4:self.page * 4 + 4]):
                y = 250 + 155 * i
                draw_text(surface, name, a.small_font, WHITE, 90, y - 7)
                draw_text(surface, f"MATERIAIS: {p['materials'].get(name, 0)}/9",
                          a.small_font, GOLD, 90, y + 18)
                self._button(surface, (90, y + 48, 430, 62), f'MATERIAL +1 · {MATERIAL_PRICE} OURO',
                    lambda n=name: self._notify(purchase_material(self.save_manager, self.save_data, n)))
                copies = [c for c in p['copies'] if c['name'] == name]
                for j, c in enumerate(copies):
                    equipped = c['id'] in p['copy_slots']
                    label = f"CÓPIA {j+1} · LV{c['level']} · " + ('EQUIPADA' if equipped else 'LIVRE')
                    draw_text(surface, label, a.small_font, GOLD, 570 + j * 410, y)
                    target = dict(c, level=2)
                    card = instance_card(target)
                    label = f"EVOLUIR · 3 MAT. + {UPGRADE_PRICES[name]} OURO" if c['level'] == 1 else 'LV2'
                    self._button(surface, (555 + j * 410, y + 48, 395, 62), label,
                        lambda cid=c['id']: self._notify(upgrade_copy(self.save_manager, self.save_data, cid)),
                        c['level'] == 1 and p['upgrades_purchased'] < 3)
                    if pygame.Rect(555 + j * 410, y, 395, 115).collidepoint(self.window_manager.get_virtual_mouse_pos()):
                        self.preview = card
            self._button(surface, (550, 930, 260, 65), 'ANTERIOR', lambda: self._page(-1), self.page > 0)
            self._button(surface, (850, 930, 260, 65), 'PRÓXIMA', lambda: self._page(1), self.page + 1 < page_count)
            preview = getattr(self, 'preview', None)
            if preview:
                for i, line in enumerate(wrap_text('LV2: ' + preview.description, a.small_font, 1730)[:2]):
                    draw_text(surface, line, a.small_font, GOLD, 90, 880 + 24 * i)
                self.preview = None
        self._button(surface, (80, 930, 400, 65), 'VOLTAR AO MENU' if self.preparation else 'VOLTAR À LOJA', self._back)
        draw_text(surface, self.message[:145], a.small_font, GOLD, 80, 1030)

    def _page(self, delta):
        self.page += delta

    def _choose_preparation(self, name):
        def mutate():
            self.save_data['perfil']['preparada'] = name
            return f'{name} preparada para a próxima run.'
        self._notify(transact(self.save_manager, self.save_data, mutate))

    def _new_run(self):
        result = self.save_manager.new_run(self.save_data)
        self._notify(result)
        if result[0]:
            from src.scenes.map_scene import MapScene
            self.scene_manager.change_scene(MapScene(self.scene_manager, self.window_manager,
                self.asset_manager, self.save_manager, self.save_data))

    def _back(self):
        if self.preparation:
            from src.scenes.menu_scene import MenuScene
            scene = MenuScene(self.scene_manager, self.window_manager, self.asset_manager)
        else:
            from src.scenes.shop_scene import ShopScene
            scene = ShopScene(self.scene_manager, self.window_manager, self.asset_manager,
                              self.save_manager, self.save_data)
        self.scene_manager.change_scene(scene)

    def handle_event(self, event):
        if self.window_manager.handle_window_event(event):
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            point = self.window_manager.map_to_virtual(event.pos)
            for rect, action, enabled in self.buttons:
                if enabled and rect.collidepoint(point):
                    action()
                    break
