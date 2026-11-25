"""Gera apenas checkpoints de QA em build/, sem alterar slots reais nem regras do jogo."""

from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json,tempfile
from copy import deepcopy
from src.systems.save_manager import SaveManager
from src.systems.card_catalog import AVAILABLE_CARD_POOL
from src.systems.territory_map import TERRITORIES
from src.systems.combat_engine import CombatEngine
from src.systems.combat_snapshot import capture
out=Path("build/web-stage4/fixtures");out.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as folder:
 m=SaveManager(folder)
 for level in range(1,8):
  for index in (0,1,None):
   data=m._normalize(m._new_data("Campanha QA","slot_1"),"slot_1")
   p=data["progresso"]
   for k in ("tutorial_concluido","intro_vista","pos_tutorial_visto","guia_mapa_visto"):
    data["perfil"][k]=p[k]=True
   p["tutoriais_gerenciamento"]={k:True for k in ("shop","backpack","workshop")}
   data["perfil"]["tutoriais_gerenciamento"]=deepcopy(p["tutoriais_gerenciamento"])
   p["territorios_desbloqueados"]=[t.id for t in TERRITORIES[:level]]
   p["territorios_concluidos"]=[t.id for t in TERRITORIES[:level-1]]
   p["encontros_por_territorio"]={t.id:2 for t in TERRITORIES[:level-1]}
   p["encontros_por_territorio"][TERRITORIES[level-1].id]=2 if index is None else index
   p["cartas_colecao"]=["Lança Perfurante","Soco Simples","Esfera Protetora"]
   data["perfil"]["vida"]=3
   p["bonus_vida_permanente"]=15
   p["melhorias_vida_run"]=3
   selected_ultimate=("mana_ancestral","forcas_ancestrais","rugido_da_floresta")[(level-1)%3]
   data["perfil"]["ultimate_equipada"]=p["ultimate_equipada"]=selected_ultimate
   p["andar"]=level
   p["moedas"]=1000
   p["materials"]={"Soco Simples":3}
   deck=["Lança Perfurante"]*3+["Soco Simples"]*3
   p["deck_slots"]=deck+[None]*12;p["cartas"]=deck
   data=m._normalize(data,"slot_1")
   engine=CombatEngine(map_mode=True)
   engine.resume_from_save(data,m,level=level,encounter_kind="point" if index is None else "road",encounter_index=index)
   if index is not None:
    from unittest.mock import patch
    from src.systems.enemy_factory import create_road_enemy,choose_next_action
    from src.systems.normal_enemy_catalog import BIOME_ENEMIES
    with patch("src.systems.enemy_factory.random.choice",return_value=BIOME_ENEMIES[level][index]):
     engine.enemy=create_road_enemy(level)
    choose_next_action(engine.enemy)
   # Pré-condições explícitas de QA; não alteram regras nem inimigos do runtime.
   engine.player.max_hp=120;engine.player.hp=120
   engine.player.strength=36
   engine.player.energy_max=8;engine.player.energy=8
   engine.player.ultimate_charge=20
   if index is None and engine.enemy.special_action:
    action=engine.enemy.special_action
    engine.enemy.current_action=action
    engine.enemy.action_plan=[action]
    engine.enemy_actions_remaining=1
    engine.state="enemy_turn"
    engine.player._block_layers=[[400,10]]
   p=data["progresso"]
   p["combat_snapshot"]=capture(engine)
   p["vida"]=120
   data=m._normalize(data,"slot_1")
   name=f"{level}-"+("boss" if index is None else str(index))+".json"
   (out/name).write_text(json.dumps(m.payload(data),ensure_ascii=False),encoding="utf-8")
 print("21 checkpoints QA gerados com validação v15")

