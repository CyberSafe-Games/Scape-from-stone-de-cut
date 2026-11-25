import json
import os
import re
from copy import deepcopy
from uuid import uuid4
from datetime import datetime

from src.config.settings import SAVES_DIR
from src.models.player import Player
from src.config.shop_balance import HEAL_LIMIT
from src.systems.card_catalog import AVAILABLE_CARD_POOL, create_starting_deck
from src.systems.card_definitions import migrate_card_name
from src.systems.territory_map import TERRITORY_IDS, FIRST_TERRITORY_ID, ROAD_FIGHTS
from src.models.effects.ultimate_effect import DEFAULT_ULTIMATE_ID, known_ultimate_ids
from src.systems.deck_loadout import INITIAL_SLOTS, normalize_collection_and_slots, deck_cards, COPIES_PER_CARD

# v9: deck equipado passa a ser uma cópia por espaço (DECK_SLOT_LIMIT).
# Saves v8 (e anteriores) migram em normalize_collection_and_slots: cada
# tipo equipado (3 cópias) vira três espaços individuais.
# v11: registra as cutscenes vistas, com defaults em _normalize().
# v12: abandona a carga de Ultimate persistida entre combates.
# v14: persiste as três compras de cura e seus preços progressivos por run.
# v15: registra os guias vistos por tela no perfil permanente do slot.
SAVE_VERSION = 15
# Somente compatibilidade: bônus comprados antes da troca da loja por cura.
# Nenhuma compra nova incrementa este contador; new_run() o zera.
HEALTH_UPGRADE_AMOUNT = 15
HEALTH_UPGRADE_LIMIT = 3
SLOT_COUNT = 3

# Território disponível em um save novo (ids de território definidos pelo jogo).
INITIAL_TERRITORIES = [FIRST_TERRITORY_ID]
INITIAL_COINS = 0
TEST_SAVE_ID = 'modo_teste'


def player_max_hp(progress):
    return (Player.BASE_HP + progress.get('bonus_vida_permanente', 0)
            + HEALTH_UPGRADE_AMOUNT * progress.get("melhorias_vida_run", 0))


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

    def __init__(self, saves_dir=SAVES_DIR, store=None):
        from src.storage.disk_store import DiskStore
        self.store = store if store is not None else DiskStore(saves_dir)
        self.saves_dir = saves_dir
        self._card_catalog = {card.name: card for card in AVAILABLE_CARD_POOL}

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
                "tutoriais_gerenciamento": {"shop": False, "backpack": False, "workshop": False},
                "tutorial_concluido": False,
                "intro_vista": False,
                "pos_tutorial_visto": False,
                "moedas": INITIAL_COINS,
                "melhorias_vida_run": 0,
                "curas_loja_run": 0,
                "cartas": deck_cards(INITIAL_SLOTS),
                "cartas_colecao": ["Soco Simples", "Esfera Protetora"],
                "deck_slots": list(INITIAL_SLOTS),
                "encontros_por_territorio": {},
                # Checkpoint reiniciado no começo de um combate (não é um snapshot do turno).
                "andar": 1,
                "vida": Player.BASE_HP,
                "energia_maxima": 2,
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
        return self.store.exists_sync(self._make_id(name))

    def list_saves(self):
        """Lista resumos dos saves existentes, do mais recente ao mais antigo."""
        summaries = []
        for save_id in self.store.keys_sync():
            filename = save_id + ".json"
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
            data = self.store.read_sync(os.path.splitext(os.path.basename(path))[0])
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise SaveCorruptedError(f"Não foi possível ler '{path}'.") from exc
        if not isinstance(data, dict):
            raise SaveCorruptedError('Estrutura de save inválida.')
        if type(data.get('versao', 0)) is not int:
            raise SaveCorruptedError('Versão de save inválida.')
        from src.storage.disk_store import DiskStore
        if isinstance(self.store, DiskStore) and data.get('versao', 0) < SAVE_VERSION:
            backup = path + f".v{data.get('versao', 0)}.bak"
            if not os.path.exists(backup):
                import shutil
                shutil.copy2(path, backup)
        return self._normalize(data, os.path.splitext(os.path.basename(path))[0])

    def _normalize(self, data, save_id):
        """Valida o conteúdo e completa campos que estejam faltando."""
        if isinstance(data, dict) and 'perfil' in data and not isinstance(data['perfil'], dict):
            raise SaveCorruptedError('Perfil inválido.')
        if isinstance(data, dict) and type(data.get('versao', 0)) is not int:
            raise SaveCorruptedError('Versão de save inválida.')
        legacy = isinstance(data, dict) and data.get('versao', 0) < SAVE_VERSION
        if isinstance(data, dict) and isinstance(data.get('run'), dict) and 'progresso' not in data:
            data['progresso'] = data['run']
            from src.systems.roguelite import PROFILE_FIELDS
            for key in PROFILE_FIELDS:
                if key in data.get('perfil', {}):
                    data['progresso'][key] = deepcopy(data['perfil'][key])
        if isinstance(data, dict) and data.get('versao', 0) > SAVE_VERSION:
            raise SaveCorruptedError('Versão futura de save não suportada.')
        if not isinstance(data, dict) or not isinstance(data.get("progresso"), dict):
            raise SaveCorruptedError("Estrutura de save inválida.")

        if not isinstance(data.get("nome", save_id), str):
            raise SaveCorruptedError("Identificação do save inválida.")
        base = self._new_data(data.get("nome", save_id), save_id)
        progress = data["progresso"]
        progress.setdefault('retomada_legada', legacy)
        if 'perfil' in data:
            progress['bonus_vida_permanente'] = 5 * data['perfil'].get('vida', 0)
        progress.pop("carga_ultimate", None)  # Campo obsoleto dos saves anteriores.
        # Saves anteriores ao tutorial já têm jornada iniciada: não obrigá-los
        # a refazer o treinamento. Apenas novos saves recebem False.
        progress.setdefault("tutorial_concluido", True)
        progress.setdefault("intro_vista", True)
        progress.setdefault("pos_tutorial_visto", True)
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
        # v9: a migração de saves antigos acontece em normalize_collection_and_slots
        # (6 espaços de tipos -> 18 espaços individuais).
        normalize_collection_and_slots(progress)
        # Saves anteriores (sem rota) preservam o acesso aos confrontos que
        # já estavam disponíveis.
        if "encontros_por_territorio" not in progress:
            progress["encontros_por_territorio"] = {
                tid: ROAD_FIGHTS for tid in progress.get("territorios_desbloqueados", [])
                if tid in TERRITORY_IDS
            }
        # Curas antigas não contam como compras da nova melhoria.
        progress.pop("curas_compradas_run", None)
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
        heals = progress['curas_loja_run']
        if type(heals) is not int or not 0 <= heals <= HEAL_LIMIT:
            raise SaveCorruptedError('Contador de curas da loja inválido.')
        upgrades = progress["melhorias_vida_run"]
        if type(upgrades) is not int or not 0 <= upgrades <= HEALTH_UPGRADE_LIMIT:
            raise SaveCorruptedError("Contador de melhorias de vida da run inválido.")
        if not isinstance(progress["cartas"], list):
            raise SaveCorruptedError("Lista de cartas inválida.")
        steps = progress.get("encontros_por_territorio", {})
        if (not isinstance(steps, dict) or any(
            key not in TERRITORY_IDS or type(value) is not int or not 0 <= value <= 3
            for key, value in steps.items()
        )):
            raise SaveCorruptedError("Contador de encontros inválido.")
        # A rota antiga aceitava três vitórias. Duas mantêm o chefe liberado.
        progress["encontros_por_territorio"] = {
            territory: min(wins, ROAD_FIGHTS) for territory, wins in steps.items()
        }

        if not isinstance(progress["territorios_desbloqueados"], list):
            raise SaveCorruptedError("Lista de territórios inválida.")
        if not isinstance(progress["territorios_concluidos"], list):
            raise SaveCorruptedError("Lista de territórios concluídos inválida.")
        if type(progress["guia_mapa_visto"]) is not bool:
            raise SaveCorruptedError("Indicador do guia inválido.")
        if type(progress["tutorial_concluido"]) is not bool:
            raise SaveCorruptedError("Indicador de tutorial inválido.")
        if type(progress["intro_vista"]) is not bool:
            raise SaveCorruptedError("Indicador de introdução inválido.")
        if type(progress["pos_tutorial_visto"]) is not bool:
            raise SaveCorruptedError("Indicador de pós-tutorial inválido.")

        for field in ("andar", "vida", "energia_maxima", "turnos"):
            if type(progress[field]) is not int or progress[field] < 0:
                raise SaveCorruptedError(f"Campo de progresso inválido: {field}.")
        if progress["andar"] < 1 or progress["vida"] > player_max_hp(progress) or not 1 <= progress["energia_maxima"] <= 8:
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
        from src.systems.roguelite import normalize_profile
        try:
            normalize_profile(data)
            if progress['combat_snapshot'] is not None:
                from src.systems.combat_snapshot import validate
                validate(progress['combat_snapshot'])
        except (ValueError, KeyError, TypeError) as exc:
            raise SaveCorruptedError(str(exc)) from exc
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
        if self.store.exists_sync(save_id):
            raise SaveAlreadyExistsError(f"Já existe um save chamado '{name}'.")
        data = self._new_data(display_name or name.strip(), save_id)
        self.save(data)
        return data

    def load_save(self, name):
        """Carrega o progresso de um save existente."""
        path = self._path(self._make_id(name))
        if not self.store.exists_sync(self._make_id(name)):
            raise SaveNotFoundError(f"Save '{name}' não encontrado.")
        return self._read(path)

    @staticmethod
    def _unlock_test_progress(progress):
        progress['territorios_desbloqueados'] = list(TERRITORY_IDS)
        progress['territorios_concluidos'] = list(TERRITORY_IDS)
        progress['encontros_por_territorio'] = {tid: ROAD_FIGHTS for tid in TERRITORY_IDS}
        progress['cartas_colecao'] = list(dict.fromkeys(
            progress['cartas_colecao'] + [card.name for card in AVAILABLE_CARD_POOL]
        ))
        progress['ultimates_desbloqueadas'] = known_ultimate_ids()
        progress['tutorial_concluido'] = True
        progress['intro_vista'] = True
        progress['pos_tutorial_visto'] = True
        progress['guia_mapa_visto'] = True
        progress['vida'] = player_max_hp(progress)

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
        test_deck_types = ['Soco Simples', 'Esfera Protetora', 'Disparo de Arco',
                           'Bola de Fogo', 'Adaga Sangrenta', 'Surto de Energia']
        progress['deck_slots'] = [
            name for name in test_deck_types for _ in range(COPIES_PER_CARD)
        ]  # Um espaço por cópia: 18 espaços, 3 de cada tipo.
        progress['cartas'] = list(progress['deck_slots'])
        self.save(data)
        return data

    def payload(self, data):
        """Representação v15 compartilhada por disco, IndexedDB e backup manual."""
        from src.systems.roguelite import PROFILE_FIELDS
        payload = {k: deepcopy(v) for k,v in data.items() if k != "progresso"}
        payload["run"] = {k:deepcopy(v) for k,v in data["progresso"].items() if k not in PROFILE_FIELDS}
        return payload

    def save(self, data):
        """Valida/migra e confirma atomicamente no backend síncrono."""
        data["atualizado_em"] = self._now()
        save_id = data.get("id")
        if not isinstance(save_id,str) or save_id != self._make_id(save_id):
            raise SaveCorruptedError("Identificador do save inválido.")
        self._normalize(data,save_id)
        from src.storage.base import StorageError
        try:
            revision = self.store.commit_sync(save_id,self.payload(data),data.get("revisao",0))
        except StorageError as exc:
            raise SaveError(str(exc)) from exc
        data["revisao"] = revision

    def delete_save(self, name):
        self.store.delete_sync(self._make_id(name))

    def export_json(self, name):
        return json.dumps(self.payload(self.load_save(name)),ensure_ascii=False,indent=4)

    def import_json(self, text, slot, replace=False):
        """Importa somente JSON validado e preserva revisão/estado do destino."""
        save_id = self.slot_id(slot)
        if len(text.encode("utf-8")) > 5*1024*1024:
            raise SaveCorruptedError("Backup maior que 5 MiB.")
        try:
            data = json.loads(text)
        except (ValueError,UnicodeError) as exc:
            raise SaveCorruptedError("Backup JSON inválido.") from exc
        if not isinstance(data,dict) or data.get("modo_teste"):
            raise SaveCorruptedError("Use um backup de jornada normal.")
        data = self._normalize(data,save_id)
        data["id"] = save_id
        if self.exists(save_id):
            if not replace:
                raise SaveAlreadyExistsError("Confirme a substituição do espaço ocupado.")
            current = self.load_save(save_id)
            data["revisao"] = current.get("revisao",0)
        else:
            data["revisao"] = 0
        self.save(data)
        return data

    def end_run(self, data, level):
        """Confirma a morte em disco antes de permitir outra jornada."""
        from src.systems.roguelite import transact
        def mutate():
            p = data['progresso']
            if is_test_save(data):
                return 'Laboratório preservado.'
            p['estado'] = 'morta'
            p['vida'] = 0
            p['combat_snapshot'] = None
            data['perfil']['melhor_territorio'] = max(level, data['perfil']['melhor_territorio'])
            return 'Run encerrada. Fragmentos e melhorias permanentes preservados.'
        return transact(self, data, mutate)

    def new_run(self, data):
        """Reinicia apenas o estado temporário, mantendo o perfil do slot."""
        from src.systems.roguelite import PROFILE_FIELDS, PREPARATION, transact
        def mutate():
            if data['progresso']['estado'] == 'ativa':
                raise ValueError('A jornada atual ainda está ativa.')
            profile = data['perfil']
            fresh = self._new_data(data['nome'], data['id'])['progresso']
            for key in PROFILE_FIELDS:
                fresh[key] = deepcopy(profile[key])
            fresh.update(run_id=uuid4().hex, estado='ativa', moedas=30,
                         bonus_vida_permanente=5 * profile['vida'])
            fresh['vida'] = player_max_hp(fresh)
            choice = profile.get('preparada')
            choices = PREPARATION[:3 if profile['preparacao'] == 1 else 6]
            if profile['preparacao'] and choice in choices:
                fresh['cartas_colecao'].append(choice)
            data['progresso'] = fresh
            data['run'] = fresh
            return 'Nova run iniciada com vida cheia.'
        return transact(self, data, mutate)

    # ========================================================
    # PROGRESSO: JOGO <-> SAVE
    # ========================================================

    def apply_to_game(self, data, player, deck_manager):
        """Aplica o progresso salvo ao jogador e ao baralho."""
        progress = data["progresso"]
        if progress.get('estado', 'ativa') != 'ativa' and not is_test_save(data):
            raise SaveError('A run terminou. Inicie uma nova jornada.')
        player.invulnerable = is_test_save(data)
        player.coins = progress["moedas"]

        player.max_hp = player_max_hp(progress)
        player.hp = min(player.max_hp, progress["vida"] or player.max_hp)
        if player.invulnerable:
            player.hp = player.max_hp
        # Energia máxima e turno são propriedades da LUTA, não da RUN.
        # Dados antigos ficam aceitos no JSON apenas para compatibilidade.
        player.energy_max = player.INITIAL_ENERGY_MAX
        player.initial_energy = progress.get('energia_inicial', 2)
        player.unlocked_ultimates = [DEFAULT_ULTIMATE_ID]
        for ultimate_id in progress.get("ultimates_desbloqueadas", [DEFAULT_ULTIMATE_ID]):
            player.unlock_ultimate(ultimate_id)
        player.equip_ultimate(progress.get("ultimate_equipada", DEFAULT_ULTIMATE_ID))
        # start_combat inicia a mão/energia do primeiro turno do novo combate.
        player.turn_count = 0
        # Apenas cartas disponíveis entram no combate, inclusive em saves antigos.
        from src.systems.roguelite import normalize_inventory, instance_card
        normalize_inventory(progress)
        copies = {c['id']: c for c in progress['copies']}
        deck_manager.deck = [instance_card(copies[cid]) for cid in progress['copy_slots'] if cid]
        if not deck_manager.deck:
            deck_manager.deck = create_starting_deck()

    def update_from_game(self, data, player, deck_manager, level=None):
        """Copia o estado atual do jogador e do baralho para os dados do save."""
        progress = data["progresso"]
        progress["moedas"] = player.coins
        normalize_collection_and_slots(progress)
        for card in deck_manager.deck:
            if card.name in self._card_catalog and card.name not in progress["cartas_colecao"]:
                progress["cartas_colecao"].append(card.name)
        # O deck é configurado na mochila. Recompensas entram na coleção, não
        # entram automaticamente nos espaços individuais.
        progress["cartas"] = deck_cards(progress["deck_slots"])
        if level is not None:
            progress["andar"] = level
        progress["vida"] = player.hp
        # Cada checkpoint representa o INÍCIO da próxima luta.
        progress["energia_maxima"] = player.INITIAL_ENERGY_MAX
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
