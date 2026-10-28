import json
import os
import re
from datetime import datetime

from src.config.settings import SAVES_DIR
from src.systems.card_catalog import CARD_POOL, create_starting_deck
from src.systems.card_definitions import migrate_card_name
from src.systems.territory_map import TERRITORY_IDS, FIRST_TERRITORY_ID
from src.models.effects.ultimate_effect import DEFAULT_ULTIMATE_ID, known_ultimate_ids
from src.systems.deck_loadout import INITIAL_SLOTS, normalize_collection_and_slots, expand_slots, SLOT_COUNT, CARD_NAMES

SAVE_VERSION = 8
SLOT_COUNT = 3

# Território disponível em um save novo (ids de território definidos pelo jogo).
INITIAL_TERRITORIES = [FIRST_TERRITORY_ID]
INITIAL_COINS = 0
TEST_SAVE_ID = 'modo_teste'


def is_test_save(data):
    return data.get('id') == TEST_SAVE_ID and data.get('modo_teste') is True


class SaveError(Exception):
    """Erro base do sistema de saves."""


class SaveNotFoundError(SaveError):
    """O save solicitado não existe."""


class SaveAlreadyExistsError(SaveError):
    """Já existe um save com esse nome."""


class SaveCorruptedError(SaveError):
    """O arquivo do save está ilegível ou inválido."""


class SaveManager:
    """Cria, carrega e salva o progresso do jogador.

    Cada save é um arquivo JSON independente dentro da pasta de saves,
    portanto o progresso de um save nunca se mistura com o de outro.
    Não depende de Pygame, apenas do Player e do DeckManager.
    """

    def __init__(self, saves_dir=SAVES_DIR):
        self.saves_dir = saves_dir
        self._card_catalog = {card.name: card for card in CARD_POOL}

    # ========================================================
    # ESTRUTURA DE DADOS
    # ========================================================

    def _new_data(self, name, save_id):
        """Monta a estrutura de dados de um save novo."""
        now = self._now()
        return {
            "versao": SAVE_VERSION,
            "id": save_id,
            "nome": name,
            "criado_em": now,
            "atualizado_em": now,
            "progresso": {
                "territorios_desbloqueados": list(INITIAL_TERRITORIES),
                "territorios_concluidos": [],
                "guia_mapa_visto": False,
                "tutorial_concluido": False,
                "moedas": INITIAL_COINS,
                "curas_compradas_run": 0,
                "cartas": expand_slots(INITIAL_SLOTS),
                "cartas_colecao": ["Soco Simples", "Esfera Protetora"],
                "deck_slots": list(INITIAL_SLOTS),
                "encontros_por_territorio": {},
                # Checkpoint reiniciado no começo de um combate (não é um snapshot do turno).
                "andar": 1,
                "vida": 60,
                "energia_maxima": 2,
                "carga_ultimate": 0,
                "turnos": 1,
                "ultimate_equipada": DEFAULT_ULTIMATE_ID,
                "ultimates_desbloqueadas": known_ultimate_ids(),
            },
        }

    @staticmethod
    def slot_id(slot):
        """Identificador fixo de cada uma das três posições da tela."""
        if not isinstance(slot, int) or isinstance(slot, bool) or not 1 <= slot <= SLOT_COUNT:
            raise ValueError("Espaço de save inválido.")
        return f"slot_{slot}"

    @staticmethod
    def _now():
        return datetime.now().isoformat(timespec="seconds")

    # ========================================================
    # ARQUIVOS
    # ========================================================

    @staticmethod
    def _make_id(name):
        """Converte o nome do save em um id seguro para nome de arquivo."""
        save_id = re.sub(r"[^a-z0-9_-]+", "_", name.strip().lower()).strip("_")
        if not save_id:
            raise ValueError("O nome do save não pode ser vazio.")
        return save_id

    def _path(self, save_id):
        return os.path.join(self.saves_dir, save_id + ".json")

    def exists(self, name):
        return os.path.exists(self._path(self._make_id(name)))

    def list_saves(self):
        """Lista resumos dos saves existentes, do mais recente ao mais antigo."""
        if not os.path.isdir(self.saves_dir):
            return []

        summaries = []
        for filename in os.listdir(self.saves_dir):
            if not filename.endswith(".json"):
                continue
            try:
                data = self._read(os.path.join(self.saves_dir, filename))
            except SaveCorruptedError:
                continue
            summaries.append(
                {
                    "id": data["id"],
                    "nome": data["nome"],
                    "atualizado_em": data["atualizado_em"],
                    "moedas": data["progresso"]["moedas"],
                    "cartas": len(data["progresso"]["cartas"]),
                    "territorios": len(data["progresso"]["territorios_desbloqueados"]),
                    "andar": data["progresso"]["andar"],
                }
            )
        summaries.sort(key=lambda s: s["atualizado_em"], reverse=True)
        return summaries

    def _read(self, path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise SaveCorruptedError(f"Não foi possível ler '{path}'.") from exc
        return self._normalize(data, os.path.splitext(os.path.basename(path))[0])

    def _normalize(self, data, save_id):
        """Valida o conteúdo e completa campos que estejam faltando."""
        if not isinstance(data, dict) or not isinstance(data.get("progresso"), dict):
            raise SaveCorruptedError("Estrutura de save inválida.")

        if not isinstance(data.get("nome", save_id), str):
            raise SaveCorruptedError("Identificação do save inválida.")
        base = self._new_data(data.get("nome", save_id), save_id)
        progress = data["progresso"]
        # Saves anteriores ao tutorial já têm jornada iniciada: não obrigá-los
        # a refazer o treinamento. Apenas novos saves recebem False.
        progress.setdefault("tutorial_concluido", True)
        if "territorios_desbloqueados" not in progress:
            progress["territorios_desbloqueados"] = list(INITIAL_TERRITORIES)
        # Migração dos saves v2: andares avançados significam fases anteriores
        # vencidas. Mantém os dados originais e ids externos já gravados.
        if "territorios_concluidos" not in progress:
            previous_floor = progress.get("andar", 1)
            if type(previous_floor) is int and previous_floor >= 1:
                previous_floor = min(previous_floor, len(TERRITORY_IDS))
                progress["territorios_concluidos"] = list(TERRITORY_IDS[:previous_floor - 1])
                unlocked = progress.get("territorios_desbloqueados")
                if isinstance(unlocked, list):
                    for tid in TERRITORY_IDS[:previous_floor]:
                        if tid not in unlocked:
                            unlocked.append(tid)
        normalize_collection_and_slots(progress)
        # Saves anteriores (sem rota) preservam o acesso aos confrontos que
        # já estavam disponíveis; novas jornadas começam com 0/3 encontros.
        if "encontros_por_territorio" not in progress:
            progress["encontros_por_territorio"] = {
                tid: 3 for tid in progress.get("territorios_desbloqueados", [])
                if tid in TERRITORY_IDS
            }
        for key, default in base["progresso"].items():
            progress.setdefault(key, default)

        if not isinstance(progress.get("ultimates_desbloqueadas"), list):
            progress["ultimates_desbloqueadas"] = [DEFAULT_ULTIMATE_ID]
        valid_ids = set(known_ultimate_ids())
        unlocked = []
        for ultimate_id in progress["ultimates_desbloqueadas"]:
            if isinstance(ultimate_id, str) and ultimate_id in valid_ids and ultimate_id not in unlocked:
                unlocked.append(ultimate_id)
        if DEFAULT_ULTIMATE_ID not in unlocked:
            unlocked.insert(0, DEFAULT_ULTIMATE_ID)
        # As três habilidades são alternativas de preparação, sem bloqueio
        # de campanha. Migra também runs criadas antes da seleção na mochila.
        for ultimate_id in known_ultimate_ids():
            if ultimate_id not in unlocked:
                unlocked.append(ultimate_id)
        progress["ultimates_desbloqueadas"] = unlocked
        if not isinstance(progress.get("ultimate_equipada"), str) or progress["ultimate_equipada"] not in unlocked:
            progress["ultimate_equipada"] = DEFAULT_ULTIMATE_ID

        if type(progress["moedas"]) is not int or progress["moedas"] < 0:
            raise SaveCorruptedError("Valor de moedas inválido.")
        if type(progress["curas_compradas_run"]) is not int or not 0 <= progress["curas_compradas_run"] <= 3:
            raise SaveCorruptedError("Contador de curas da RUN inválido.")
        if not isinstance(progress["cartas"], list):
            raise SaveCorruptedError("Lista de cartas inválida.")
        steps = progress.get("encontros_por_territorio", {})
        if (not isinstance(steps, dict) or any(
            key not in TERRITORY_IDS or type(value) is not int or not 0 <= value <= 3
            for key, value in steps.items()
        )):
            raise SaveCorruptedError("Contador de encontros inválido.")

        if not isinstance(progress["territorios_desbloqueados"], list):
            raise SaveCorruptedError("Lista de territórios inválida.")
        if not isinstance(progress["territorios_concluidos"], list):
            raise SaveCorruptedError("Lista de territórios concluídos inválida.")
        if type(progress["guia_mapa_visto"]) is not bool:
            raise SaveCorruptedError("Indicador do guia inválido.")
        if type(progress["tutorial_concluido"]) is not bool:
            raise SaveCorruptedError("Indicador de tutorial inválido.")

        for field in ("andar", "vida", "energia_maxima", "carga_ultimate", "turnos"):
            if type(progress[field]) is not int or progress[field] < 0:
                raise SaveCorruptedError(f"Campo de progresso inválido: {field}.")
        if progress["andar"] < 1 or progress["vida"] > 60 or not 1 <= progress["energia_maxima"] <= 8:
            raise SaveCorruptedError("Checkpoint inválido.")
        if any(not isinstance(card, str) for card in progress["cartas"]):
            raise SaveCorruptedError("Lista de cartas inválida.")
        if any(not isinstance(territory, str) for territory in progress["territorios_desbloqueados"]):
            raise SaveCorruptedError("Lista de territórios inválida.")
        if any(not isinstance(territory, str) for territory in progress["territorios_concluidos"]):
            raise SaveCorruptedError("Lista de territórios concluídos inválida.")
        data['versao'] = SAVE_VERSION
        data["id"] = save_id  # O nome real do arquivo prevalece sobre o conteúdo.
        if 'modo_teste' in data and type(data['modo_teste']) is not bool:
            raise SaveCorruptedError('Indicador de modo de teste inválido.')
        if is_test_save(data):
            self._unlock_test_progress(progress)
        data.setdefault("nome", save_id)
        data.setdefault("criado_em", base["criado_em"])
        data.setdefault("atualizado_em", base["atualizado_em"])
        return data

    # ========================================================
    # CRIAR, CARREGAR E SALVAR
    # ========================================================

    def create_save(self, name, display_name=None):
        """Cria um save novo (sem sobrescrever um existente) e o retorna."""
        save_id = self._make_id(name)
        if os.path.exists(self._path(save_id)):
            raise SaveAlreadyExistsError(f"Já existe um save chamado '{name}'.")
        data = self._new_data(display_name or name.strip(), save_id)
        self.save(data)
        return data

    def load_save(self, name):
        """Carrega o progresso de um save existente."""
        path = self._path(self._make_id(name))
        if not os.path.exists(path):
            raise SaveNotFoundError(f"Save '{name}' não encontrado.")
        return self._read(path)

    @staticmethod
    def _unlock_test_progress(progress):
        progress['territorios_desbloqueados'] = list(TERRITORY_IDS)
        progress['territorios_concluidos'] = list(TERRITORY_IDS)
        progress['encontros_por_territorio'] = {tid: 3 for tid in TERRITORY_IDS}
        progress['cartas_colecao'] = [card.name for card in CARD_POOL]
        progress['ultimates_desbloqueadas'] = known_ultimate_ids()
        progress['tutorial_concluido'] = True
        progress['guia_mapa_visto'] = True
        progress['vida'] = 60

    def load_or_create_test_save(self):
        """Save extra identificado explicitamente; não ocupa nem substitui slots."""
        if self.exists(TEST_SAVE_ID):
            data = self.load_save(TEST_SAVE_ID)
            if not is_test_save(data):
                raise SaveError('O arquivo modo_teste já existe e não é um save de testes.')
            return data
        data = self._new_data('Laboratório de Testes', TEST_SAVE_ID)
        data['modo_teste'] = True
        progress = data['progresso']
        self._unlock_test_progress(progress)
        progress['andar'] = 7
        progress['moedas'] = 9999
        progress['deck_slots'] = ['Soco Simples', 'Esfera Protetora', 'Disparo de Arco',
                                  'Bola de Fogo', 'Adaga Sangrenta', 'Surto de Energia']
        progress['cartas'] = expand_slots(progress['deck_slots'])
        self.save(data)
        return data

    def save(self, data):
        """Grava os dados no arquivo do próprio save (e só nele)."""
        os.makedirs(self.saves_dir, exist_ok=True)
        data["atualizado_em"] = self._now()
        data["versao"] = SAVE_VERSION

        # Impede criação de caminhos arbitrários via um dicionário manipulado.
        save_id = data.get("id")
        if not isinstance(save_id, str) or save_id != self._make_id(save_id):
            raise SaveCorruptedError("Identificador do save inválido.")
        self._normalize(data, save_id)
        path = self._path(save_id)
        tmp_path = path + ".tmp"
        # Grava num arquivo temporário e troca no final, para que um
        # fechamento inesperado do jogo não corrompa o save.
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(tmp_path, path)

    def delete_save(self, name):
        path = self._path(self._make_id(name))
        if os.path.exists(path):
            os.remove(path)

    # ========================================================
    # PROGRESSO: JOGO <-> SAVE
    # ========================================================

    def apply_to_game(self, data, player, deck_manager):
        """Aplica o progresso salvo ao jogador e ao baralho."""
        progress = data["progresso"]
        player.invulnerable = is_test_save(data)
        player.coins = progress["moedas"]

        # Cartas desconhecidas (ex: removidas do catálogo) são ignoradas.
        player.hp = min(player.max_hp, progress["vida"] or player.max_hp)
        if player.invulnerable:
            player.hp = player.max_hp
        # Energia máxima e turno são propriedades da LUTA, não da RUN.
        # Dados antigos ficam aceitos no JSON apenas para compatibilidade.
        player.energy_max = player.INITIAL_ENERGY_MAX
        player.ultimate_charge = min(player.ultimate_threshold, progress["carga_ultimate"])
        player.unlocked_ultimates = [DEFAULT_ULTIMATE_ID]
        for ultimate_id in progress.get("ultimates_desbloqueadas", [DEFAULT_ULTIMATE_ID]):
            player.unlock_ultimate(ultimate_id)
        player.equip_ultimate(progress.get("ultimate_equipada", DEFAULT_ULTIMATE_ID))
        # start_combat inicia a mão/energia do primeiro turno do novo combate.
        player.turn_count = 0
        deck_manager.deck = [
            self._card_catalog[migrate_card_name(name)].copy()
            for name in progress["cartas"]
            if migrate_card_name(name) in self._card_catalog
        ]

    def update_from_game(self, data, player, deck_manager, level=None):
        """Copia o estado atual do jogador e do baralho para os dados do save."""
        progress = data["progresso"]
        progress["moedas"] = player.coins
        normalize_collection_and_slots(progress)
        for card in deck_manager.deck:
            if card.name in CARD_NAMES and card.name not in progress["cartas_colecao"]:
                progress["cartas_colecao"].append(card.name)
        # O deck é configurado na mochila. Recompensas entram na coleção, não
        # entram automaticamente na seleção de três cópias por tipo.
        progress["cartas"] = expand_slots(progress["deck_slots"])
        if level is not None:
            progress["andar"] = level
        progress["vida"] = player.hp
        # Cada checkpoint representa o INÍCIO da próxima luta.
        progress["energia_maxima"] = player.INITIAL_ENERGY_MAX
        progress["carga_ultimate"] = player.ultimate_charge
        progress["turnos"] = 1
        progress["ultimate_equipada"] = getattr(player, "equipped_ultimate_id", DEFAULT_ULTIMATE_ID)
        unlocked = list(dict.fromkeys(getattr(player, "unlocked_ultimates", [DEFAULT_ULTIMATE_ID])))
        if DEFAULT_ULTIMATE_ID not in unlocked:
            unlocked.insert(0, DEFAULT_ULTIMATE_ID)
        progress["ultimates_desbloqueadas"] = unlocked

    @staticmethod
    def unlock_territory(data, territory_id):
        """Registra um território como desbloqueado (sem duplicar)."""
        unlocked = data["progresso"]["territorios_desbloqueados"]
        if territory_id not in unlocked:
            unlocked.append(territory_id)
