"""Efeitos dos inimigos comuns e exceções físicas básicas dos chefes."""

COMMON_ATTACK_SOUNDS = {
    "viniurgo": {"atk1": "gameplay.attack.punch", "atk2": "gameplay.attack.punch"},
    "slime": {"atk": "gameplay.enemy.slime"},
    "vinimuth": {"atk1": "gameplay.attack.punch", "atk2": "gameplay.skill.energy"},
    "esqueleto saqueador": {"atk1": "gameplay.enemy.blade", "atk2": "gameplay.attack.spear"},
    "golem das ruínas": {"atk1": "gameplay.attack.charge_impact"},
    "centauro vigia": {"atk1": "gameplay.attack.arrow_impact", "atk2": "gameplay.attack.charge_impact"},
    "putrefato do pântano": {"atk1": "gameplay.enemy.acid"},
    # O mangual usa provisoriamente impacto pesado, sem som de lâmina.
    "guerreiro da mata": {"atk1": "gameplay.attack.charge_impact", "atk2": "gameplay.attack.charge_impact"},
    "lagarto couraçado": {"atk1": "gameplay.attack.punch"},
    "morcego sombrio": {"atk1": "gameplay.attack.punch", "atk2": "gameplay.skill.energy"},
    "lutador mascarado": {"atk1": "gameplay.attack.punch", "atk2": "gameplay.attack.charge_impact"},
    "mago do santuário": {"atk1": "gameplay.attack.fireball", "atk2": "gameplay.attack.charge_impact"},
    "crocodilo abissal": {"atk1": "gameplay.attack.charge_impact"},
    "macaco selvagem": {"atk1": "gameplay.attack.punch"},
}

# Somente ações comuns sem arma ou poder; nunca aplicar a uma Ultimate.
BASIC_BOSS_ATTACK_SOUNDS = {
    "álvaro e tex · pequeno": {"atk1": "gameplay.attack.punch"},
    "gordofera": {"atk3": "gameplay.attack.charge_impact"},
}

COMMON_SUPPORT_SOUNDS = {
    "slime": {"def": "gameplay.skill.shield_light"},
    "golem das ruínas": {"def": "gameplay.skill.shield_light"},
    "lagarto couraçado": {"def": "gameplay.skill.shield_light"},
    "crocodilo abissal": {"def": "gameplay.skill.shield_light"},
    "putrefato do pântano": {"healer2": "gameplay.enemy.heal"},
    "macaco selvagem": {"healer2": "gameplay.enemy.heal"},
}

# Piloto: identidade própria do Guardião, sem alterar os demais chefes.
BOSS_ATTACK_SOUNDS = {
    "zanzara": {"atk1": "gameplay.boss.zanzara.swing", "atk2": "gameplay.boss.zanzara.smoke", "atk3": "gameplay.boss.zanzara.portal"},

    "carrasco da vigília": {"atk1": "gameplay.boss.carrasco.cut", "atk2": "gameplay.boss.carrasco.sweep"},
    "corpo seco": {"atk1": "gameplay.boss.corpo.slash", "atk3": "gameplay.boss.corpo.cross"},
    "gordofera": {"atk1": "gameplay.boss.guardian.claw", "atk2": "gameplay.boss.gordofera.roar"},
    "goblin nerd": {"atk1": "gameplay.boss.goblin.throw", "atk2": "gameplay.boss.goblin.zap", "atk3": "gameplay.boss.goblin.toxic"},
    "álvaro e tex · pequeno": {"atk2": "gameplay.boss.small.club", "atk4": "gameplay.boss.duo.star"},
    "guardião da pedra": {"atk1": "gameplay.boss.guardian.claw"},
    "álvaro e tex": {"atk1": "gameplay.boss.duo.stab", "atk2": "gameplay.boss.duo.star"},
}
BOSS_SUPPORT_SOUNDS = {
    "carrasco da vigília": {"healer2": "gameplay.boss.carrasco.vigor"},
    "corpo seco": {"def": "gameplay.boss.corpo.guard"},
    "gordofera": {"def": "gameplay.boss.gordofera.guard"},
    "goblin nerd": {"healer2": "gameplay.boss.goblin.shield"},
    "álvaro e tex": {"healer2": "gameplay.boss.duo.smoke"},
    "guardião da pedra": {
        "def": "gameplay.boss.guardian.stone",
        "healer2": "gameplay.boss.guardian.heal",
    },
}
BOSS_ULTIMATE_SOUNDS = {
    "zanzara": {"atk3": "gameplay.boss.zanzara.summon"},
    "carrasco da vigília": {"atk3": "gameplay.boss.carrasco.execution"},
    "corpo seco": {"atk4": "gameplay.boss.corpo.spin"},
    "gordofera": {"atk4": "gameplay.boss.gordofera.jump"},
    "goblin nerd": {"atk2": "gameplay.boss.goblin.beam"},
    "álvaro e tex · pequeno": {"atk3": "gameplay.boss.small.fury"},
    "álvaro e tex": {"atk4": "gameplay.boss.duo.whirl"},
    "guardião da pedra": {"atk2": "gameplay.boss.guardian.roar"},
}

SOUND_WINDOWS_MS = {
    "gameplay.boss.zanzara.souls": 2200,
    "gameplay.boss.zanzara.laugh": 3300,
    "gameplay.boss.zanzara.swing": 400,
    "gameplay.boss.zanzara.flesh": 1100,
    "gameplay.boss.zanzara.smoke": 900,
    "gameplay.boss.zanzara.aura": 1500,
    "gameplay.boss.zanzara.portal": 1300,
    "gameplay.boss.zanzara.summon": 1100,
    "gameplay.boss.zanzara.ferry": 1000,

    "gameplay.boss.carrasco.cut": 290,
    "gameplay.boss.carrasco.sweep": 320,
    "gameplay.boss.carrasco.execution": 670,
    "gameplay.boss.carrasco.execution_hit": 1400,
    "gameplay.boss.carrasco.vigor": 1500,
    "gameplay.boss.corpo.slash": 220,
    "gameplay.boss.corpo.cross": 260,
    "gameplay.boss.corpo.spin": 550,
    "gameplay.boss.corpo.guard": 1100,
    "gameplay.boss.gordofera.roar": 1800,
    "gameplay.boss.gordofera.guard": 1300,
    "gameplay.boss.gordofera.jump": 450,
    "gameplay.boss.gordofera.tremor": 1600,
    "gameplay.boss.goblin.throw": 480,
    "gameplay.boss.goblin.zap": 240,
    "gameplay.boss.goblin.energy_hit": 1600,
    "gameplay.boss.goblin.toxic": 1800,
    "gameplay.boss.goblin.retch": 820,
    "gameplay.boss.goblin.shield": 1300,
    "gameplay.boss.goblin.charge": 816,
    "gameplay.boss.goblin.beam": 792,
    "gameplay.boss.small.club": 400,
    "gameplay.boss.small.body_hit": 550,
    "gameplay.boss.small.fury": 650,
    "gameplay.boss.small.fury_hit": 800,
    "gameplay.boss.duo.stab": 400,
    "gameplay.boss.duo.star": 600,
    "gameplay.boss.duo.whirl": 700,
    "gameplay.boss.duo.flesh_hit": 1100,
    "gameplay.boss.duo.heavy_hit": 1100,
    "gameplay.boss.duo.smoke": 2100,
    "gameplay.boss.guardian.claw": 226,
    "gameplay.boss.guardian.claw_hit": 1100,
    "gameplay.boss.guardian.stone": 1100,
    "gameplay.boss.guardian.heal": 1200,
    "gameplay.boss.guardian.roar": 1500,
    "gameplay.enemy.slime": 1800,
    "gameplay.enemy.acid": 700,
    "gameplay.attack.fireball": 700,
    "gameplay.skill.energy": 600,
    "gameplay.enemy.heal": 650,
    "gameplay.attack.arrow_launch": 600,
    "gameplay.attack.arrow_impact": 350,
}
