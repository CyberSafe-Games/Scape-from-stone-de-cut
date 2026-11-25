"""Manifesto puro: propriedade única e dependências de recursos web por contexto."""
from pathlib import PurePosixPath

BOSS_SLUGS = ("guardiao_da_pedra", "alvaro_tex", "goblin_nerd", "gordofera",
              "corpo_seco", "carrasco_da_vigilia", "zanzara")
BACKGROUNDS = {1:"pedra_do_corte",2:"mata_sombria",3:"ruinas_ancestrais",
               4:"pantano_abissal",5:"fortaleza_caida",6:"pico_da_vigilia",7:"masmorra_final"}
VERSIONS = {"eight_frames","twelve_frames","sheets_eight","source"}

def enemy_owner(slug):
    for boss in BOSS_SLUGS:
        if slug.startswith(boss):return "enemy:"+boss
    return "enemy:"+slug

def owner(path):
    parts = PurePosixPath(path).parts
    if parts[0] != "assets" or ".." in parts:
        raise ValueError("Recurso fora de assets.")
    p = parts[1:]
    name = p[-1]
    if p[0] == "fonts" or name == "background.png":
        return "menu"
    if p[0] == "audio":
        if "music" in p:
            return "menu" if "menu_floresta" in name else "music:" + name
        return "menu" if "ui" in p or name in ("card-place-2.ogg","chip-lay-1.ogg") else "audio"
    if p[0] == "cutscenes":
        return "cutscene:" + ("intro" if name.startswith("intro") else
                              "post" if name.startswith(("post","pos_")) else "final")
    if name.startswith("background_"):
        for level,slug in BACKGROUNDS.items():
            if slug in name: return f"territory:{level}"
        return "tutorial" if "tutorial" in name else "management"
    if p[0] in ("player","card_effects","ultimate_effects"):
        return "player"
    if p[0] in ("bosses","boss_ultimate_effects","enemies"):
        if p[0]=="enemies" and len(p)>2 and p[1]=="defeat":
            return "combat_shared" if name.endswith(".json") else enemy_owner(PurePosixPath(name).stem)
        rest = [s for s in p[1:] if s not in VERSIONS]
        if len(rest)>1:
            slug = rest[0]
            for boss in BOSS_SLUGS:
                if slug.startswith(boss): return "enemy:"+boss
            return "enemy:"+slug
        if p[0] == "enemies" and "defeat" in p and len(p)>2:
            return "enemy:"+PurePosixPath(name).stem
        for boss in BOSS_SLUGS:
            if name.startswith(boss): return "enemy:"+boss
        return "combat_shared"
    if p[0] in ("goblin_nerd","goblin_monge","guardiao_da_pedra","slime"):
        return "enemy:"+("vinimuth" if p[0]=="goblin_monge" else p[0])
    if p[0] in ("projectiles","intent_art") and len(p)>2:
        if p[0]=="intent_art":
            slug="alvaro_tex" if p[1].startswith("alvaro_tex_phase") else p[1]
            return "enemy:"+slug
        return "combat_shared"
    return "management"

def context_groups(kind, level=1, enemy_slugs=()):
    groups={"menu"}
    if kind in ("map","management","battle","tutorial"):
        groups.add("management")
    if kind in ("battle","tutorial"):
        groups.update(("player","audio","combat_shared",f"territory:{level}"))
        groups.update("enemy:"+slug for slug in enemy_slugs)
        groups.add("music:combate_tambores_v1.ogg")
        groups.add("music:chefes_jungle_chase_v2.ogg")
        groups.add("music:chefes_jungle_tribe_v2.ogg")
        if kind=="tutorial":groups.add("tutorial")
    if kind.startswith("cutscene:"):
        groups.add(kind)
        groups.update(("music:combate_tambores_v1.ogg","music:chefes_jungle_chase_v2.ogg",
                       "music:epilogo_lost_time_v1.ogg","music:chefes_jungle_tribe_v2.ogg"))
    return groups



def working_set(kind, required, resident):
    """Conserva arquivos comuns entre mapa e combate, sem reter kits de outro bioma."""
    if kind not in ("map","management"):
        return set(required)
    shared={"player","audio","combat_shared"}
    return set(required) | {group for group in resident if group in shared or group.startswith("music:")}
