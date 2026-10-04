"""ETL Sync script for Genshin Artifact Calculator v2.

Fetches, normalizes, and packages data from:
1. MadeBaruna/paimon-moe (build.js, characters.js) -> character meta-builds
2. theBowja/genshin-db (Russian indexes, images) -> Russian localization & HoYo CDN icons
3. DimbreathBot/AnimeGameData / Game math -> roll distributions and probabilities
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request

RAW_PAIMON_BUILDS = "https://raw.githubusercontent.com/MadeBaruna/paimon-moe/main/src/data/build.js"
RAW_PAIMON_CHARS = "https://raw.githubusercontent.com/MadeBaruna/paimon-moe/main/src/data/characters.js"
RAW_GDB_CHARS_RU = "https://raw.githubusercontent.com/theBowja/genshin-db/main/src/data/index/Russian/characters.json"
RAW_GDB_ARTS_RU = "https://raw.githubusercontent.com/theBowja/genshin-db/main/src/data/index/Russian/artifacts.json"
RAW_GDB_CHARS_IMG = "https://raw.githubusercontent.com/theBowja/genshin-db/main/src/data/image/characters.json"
RAW_GDB_ARTS_IMG = "https://raw.githubusercontent.com/theBowja/genshin-db/main/src/data/image/artifacts.json"

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def fetch_url(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def parse_js_object(js_content: str, var_name: str) -> dict:
    """Extract a JavaScript export object and parse it into Python dict via Node.js."""
    import subprocess
    import tempfile
    
    # Strip ES module imports
    clean_js = re.sub(r"import\s+.*?;\s*", "", js_content)
    
    header = """
    const itemList = {};
    const elements = { pyro: 'pyro', hydro: 'hydro', electro: 'electro', cryo: 'cryo', anemo: 'anemo', geo: 'geo', dendro: 'dendro' };
    const weapons = { sword: 'sword', claymore: 'claymore', polearm: 'polearm', bow: 'bow', catalyst: 'catalyst' };
    """
    code = header + clean_js.replace(f"export const {var_name}", f"const {var_name}")
    code += f"\nconsole.log(JSON.stringify({var_name}));\n"
    
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".js", delete=False) as tmp:
        tmp.write(code)
        tmp_name = tmp.name
        
    try:
        res = subprocess.run(["node", tmp_name], capture_output=True, text=True, check=True, encoding="utf-8")
        return json.loads(res.stdout)
    finally:
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except OSError:
                pass


# Mapping from Paimon.moe stat names to standard Russian stat names
STAT_MAP_RU = {
    "ATK%": "Сила атаки %",
    "ATK": "Сила атаки",
    "Flat ATK": "Сила атаки",
    "HP%": "HP %",
    "HP": "HP",
    "Flat HP": "HP",
    "DEF%": "Защита %",
    "DEF": "Защита",
    "Flat DEF": "Защита",
    "Elemental Mastery": "Мастерство стихий",
    "Energy Recharge": "Восст. энергии",
    "Crit Rate": "Шанс крит. попадания",
    "Crit DMG": "Крит. урон",
    "Crit Rate / DMG": ["Шанс крит. попадания", "Крит. урон"],
    "Pyro DMG": "Пиро урон %",
    "Hydro DMG": "Гидро урон %",
    "Electro DMG": "Электро урон %",
    "Cryo DMG": "Крио урон %",
    "Anemo DMG": "Анемо урон %",
    "Geo DMG": "Гео урон %",
    "Dendro DMG": "Дендро урон %",
    "Physical DMG": "Физ. урон %",
    "Healing Bonus": "Бонус лечения %",
}

ELEMENT_EN_TO_RU = {
    "pyro": "Пиро",
    "hydro": "Гидро",
    "electro": "Электро",
    "cryo": "Крио",
    "anemo": "Анемо",
    "geo": "Гео",
    "dendro": "Дендро",
}

# Mapping artifact names from paimon-moe (snake_case) to standard GOOD setKey
PAIMON_SET_TO_GOOD = {
    "golden_troupe": "GoldenTroupe",
    "marechaussee_hunter": "MarechausseeHunter",
    "emblem_of_severed_fate": "EmblemOfSeveredFate",
    "deepwood_memories": "DeepwoodMemories",
    "gilded_dreams": "GildedDreams",
    "viridescent_venerer": "ViridescentVenerer",
    "obsidian_codex": "ObsidianCodex",
    "scroll_of_the_hero_of_cinder_city": "ScrollOfTheHeroOfCinderCity",
    "crimson_witch_of_flames": "CrimsonWitchOfFlames",
    "blizzard_strayer": "BlizzardStrayer",
    "tenacity_of_the_millelith": "TenacityOfTheMillelith",
    "noblesse_oblige": "NoblesseOblige",
    "ocean-hued_clam": "OceanHuedClam",
    "ocean_hued_clam": "OceanHuedClam",
    "song_of_days_past": "SongOfDaysPast",
    "flower_of_paradise_lost": "FlowerOfParadiseLost",
    "desert_pavilion_chronicle": "DesertPavilionChronicle",
    "nymphs_dream": "NymphsDream",
    "vourukashas_glow": "VourukashasGlow",
    "fragment_of_harmonic_whimsy": "FragmentOfHarmonicWhimsy",
    "unfinished_reverie": "UnfinishedReverie",
    "husk_of_opulent_dreams": "HuskOfOpulentDreams",
    "shimenawas_reminiscence": "ShimenawasReminiscence",
    "gladiators_finale": "GladiatorsFinale",
    "wanderers_troupe": "WanderersTroupe",
    "heart_of_depth": "HeartOfDepth",
    "thundering_fury": "ThunderingFury",
    "nighttime_whispers_in_the_echoing_woods": "NighttimeWhispersInTheEchoingWoods",
    "instructor": "Instructor",
    "the_exile": "TheExile",
    "scholar": "Scholar",
    "berserker": "Berserker",
    "archaic_petra": "ArchaicPetra",
    "bloodstained_chivalry": "BloodstainedChivalry",
    "maiden_beloved": "MaidenBeloved",
    "lavawalker": "Lavawalker",
    "thundersoother": "Thundersoother",
    "pale_flame": "PaleFlame",
    "echoes_of_an_offering": "EchoesOfAnOffering",
    "vermillion_hereafter": "VermillionHereafter",
}


def paimon_set_to_good_key(paimon_key: str) -> str:
    """Normalize paimon artifact key to GOOD setKey."""
    key = paimon_key.strip().lower()
    if key in PAIMON_SET_TO_GOOD:
        return PAIMON_SET_TO_GOOD[key]
    # Remove special chars and convert to CamelCase
    clean = re.sub(r"[^a-zA-Z0-9]", " ", key)
    words = clean.split()
    return "".join(w.capitalize() for w in words)


def calculate_substat_weights(substat_list: list[str]) -> dict[str, float]:
    """Calculate normalized weights for substats based on priority ranking in Paimon.moe."""
    weights: dict[str, float] = {
        "Крит. урон": 0.0,
        "Шанс крит. попадания": 0.0,
        "Сила атаки %": 0.0,
        "Сила атаки": 0.0,
        "HP %": 0.0,
        "HP": 0.0,
        "Защита %": 0.0,
        "Защита": 0.0,
        "Восст. энергии": 0.0,
        "Мастерство стихий": 0.0,
    }

    tier_weights = [2.0, 1.5, 1.0, 0.7, 0.4, 0.2]

    for rank, item in enumerate(substat_list):
        w = tier_weights[rank] if rank < len(tier_weights) else 0.2
        mapped = STAT_MAP_RU.get(item, item)
        if isinstance(mapped, list):
            for m in mapped:
                if m in weights:
                    weights[m] = max(weights[m], w)
        elif isinstance(mapped, str):
            if mapped in weights:
                # Flat stats receive reduced weight relative to their percentage counterpart
                if mapped in ("Сила атаки", "HP", "Защита"):
                    weights[mapped] = max(weights[mapped], round(w * 0.3, 1))
                else:
                    weights[mapped] = max(weights[mapped], w)

    # Ensure baseline minimum flat weights if corresponding % stat is valued
    for stat_pct, stat_flat in [("Сила атаки %", "Сила атаки"), ("HP %", "HP"), ("Защита %", "Защита")]:
        if weights[stat_pct] >= 1.0 and weights[stat_flat] == 0.0:
            weights[stat_flat] = 0.2

    return weights


def sync_all():
    os.makedirs(DATA_DIR, exist_ok=True)

    print("1. Fetching genshin-db Russian indexes and image maps...")
    gdb_chars_ru = json.loads(fetch_url(RAW_GDB_CHARS_RU))["namemap"]
    gdb_arts_ru = json.loads(fetch_url(RAW_GDB_ARTS_RU))["namemap"]
    gdb_chars_img = json.loads(fetch_url(RAW_GDB_CHARS_IMG))

    print("2. Fetching Paimon.moe builds and character metadata...")
    paimon_builds_js = fetch_url(RAW_PAIMON_BUILDS)
    paimon_chars_js = fetch_url(RAW_PAIMON_CHARS)

    paimon_builds = parse_js_object(paimon_builds_js, "builds")
    paimon_chars = parse_js_object(paimon_chars_js, "characters")

    # ──────────────────────────────────────────────────────────────────
    # A. Build characters_meta.json
    # ──────────────────────────────────────────────────────────────────
    print("3. Building characters_meta.json...")
    chars_meta = {}
    for char_id, p_info in paimon_chars.items():
        # Clean id
        cid_clean = char_id.lower().replace("_", "").replace("-", "")
        # Russian name from genshin-db or paimon
        name_ru = gdb_chars_ru.get(cid_clean, p_info.get("name", char_id))
        element_en = p_info.get("element", "anemo").lower()
        element_ru = ELEMENT_EN_TO_RU.get(element_en, "Анемо")
        rarity = p_info.get("rarity", 5)

        img_info = gdb_chars_img.get(cid_clean, {})
        icon_url = img_info.get("mihoyo_icon", img_info.get("hoyolab-avatar", ""))
        side_icon_url = img_info.get("mihoyo_sideIcon", "")

        chars_meta[char_id] = {
            "id": char_id,
            "name_ru": name_ru,
            "name_en": p_info.get("name", char_id.capitalize()),
            "element": element_ru,
            "element_en": element_en,
            "rarity": rarity,
            "weapon_type": p_info.get("weapon", "sword"),
            "icon_url": icon_url,
            "side_icon_url": side_icon_url,
        }

    with open(os.path.join(DATA_DIR, "characters_meta.json"), "w", encoding="utf-8") as f:
        json.dump(chars_meta, f, ensure_ascii=False, indent=2)

    # ──────────────────────────────────────────────────────────────────
    # B. Build artifacts_ru.json
    # ──────────────────────────────────────────────────────────────────
    print("4. Building artifacts_ru.json...")
    artifacts_ru = {}
    for gdb_key, name_ru in gdb_arts_ru.items():
        good_key = paimon_set_to_good_key(gdb_key)
        artifacts_ru[good_key] = {
            "good_key": good_key,
            "name_ru": name_ru,
            "description": f"Комплект артефактов «{name_ru}»",
        }

    # Ensure all sets from character_builds.py exist
    from character_builds import ARTIFACT_SETS as EXISTING_SETS
    for k, v in EXISTING_SETS.items():
        if k not in artifacts_ru:
            artifacts_ru[k] = {
                "good_key": k,
                "name_ru": v["name_ru"],
                "description": v.get("description", ""),
            }
        else:
            if "description" in v and len(v["description"]) > len(artifacts_ru[k]["description"]):
                artifacts_ru[k]["description"] = v["description"]

    with open(os.path.join(DATA_DIR, "artifacts_ru.json"), "w", encoding="utf-8") as f:
        json.dump(artifacts_ru, f, ensure_ascii=False, indent=2)

    # Reverse lookup for set names
    set_name_to_key = {v["name_ru"]: k for k, v in artifacts_ru.items()}

    # ──────────────────────────────────────────────────────────────────
    # C. Build builds.json
    # ──────────────────────────────────────────────────────────────────
    print("5. Processing character builds from Paimon.moe...")
    builds_list = []

    for char_id, char_data in paimon_builds.items():
        meta = chars_meta.get(char_id, {})
        char_name_ru = meta.get("name_ru", char_id.capitalize())
        element_ru = meta.get("element", "Анемо")

        roles = char_data.get("roles", {})
        for role_name, role_info in roles.items():
            # Main stats
            raw_mains = role_info.get("mainStats", {})
            sands_list = [STAT_MAP_RU.get(s, s) for s in raw_mains.get("sands", ["Сила атаки %"])]
            goblet_list = [STAT_MAP_RU.get(g, g) for g in raw_mains.get("goblet", [f"{element_ru} урон %"])]
            circlet_list = []
            for c in raw_mains.get("circlet", ["Крит. урон", "Шанс крит. попадания"]):
                mapped = STAT_MAP_RU.get(c, c)
                if isinstance(mapped, list):
                    circlet_list.extend(mapped)
                else:
                    circlet_list.append(mapped)

            # Flatten any list values
            def flatten_stats(stats):
                out = []
                for s in stats:
                    if isinstance(s, list):
                        out.extend(s)
                    else:
                        out.append(s)
                return out

            main_stats = {
                "Пески времени": flatten_stats(sands_list),
                "Кубок пространства": flatten_stats(goblet_list),
                "Корона разума": flatten_stats(circlet_list),
            }

            # Artifact sets
            best_sets_ru = []
            good_keys = []
            raw_arts = role_info.get("artifacts", [])
            for art_group in raw_arts:
                for art_item in art_group:
                    if art_item.startswith("+"):
                        continue  # Skip generic bonuses like +18%_atk_set
                    good_k = paimon_set_to_good_key(art_item)
                    if good_k in artifacts_ru:
                        name_ru = artifacts_ru[good_k]["name_ru"]
                        if name_ru not in best_sets_ru:
                            best_sets_ru.append(name_ru)
                        if good_k not in good_keys:
                            good_keys.append(good_k)

            # Substats weights
            substats_raw = role_info.get("subStats", [])
            substat_weights = calculate_substat_weights(substats_raw)

            # Weapons
            weapons = role_info.get("weapons", [])

            # Notes
            note_str = role_info.get("tip", "")
            if role_info.get("note"):
                note_clean = re.sub(r"<[^>]+>", "", role_info.get("note", ""))
                note_str = f"{note_str}\n\n{note_clean}".strip()

            builds_list.append({
                "char_id": char_id,
                "name": char_name_ru,
                "build_name": role_name,
                "element": element_ru,
                "role": role_name,
                "recommended": role_info.get("recommended", False),
                "best_sets": best_sets_ru or ["Золотая труппа"],
                "good_set_keys": good_keys or ["GoldenTroupe"],
                "main_stats": main_stats,
                "substat_weights": substat_weights,
                "weapons": weapons[:5],
                "notes": note_str[:500] if note_str else "",
            })

    with open(os.path.join(DATA_DIR, "builds.json"), "w", encoding="utf-8") as f:
        json.dump(builds_list, f, ensure_ascii=False, indent=2)

    # ──────────────────────────────────────────────────────────────────
    # D. Build relic_math.json
    # ──────────────────────────────────────────────────────────────────
    print("6. Generating relic_math.json (AnimeGameData precision math)...")
    relic_math = {
        "discrete_rolls_5star": {
            "Крит. урон": [5.44, 6.22, 6.99, 7.77],
            "Шанс крит. попадания": [2.72, 3.11, 3.50, 3.89],
            "Сила атаки %": [4.08, 4.66, 5.25, 5.83],
            "Защита %": [5.10, 5.83, 6.56, 7.29],
            "HP %": [4.08, 4.66, 5.25, 5.83],
            "Мастерство стихий": [16.32, 18.65, 20.98, 23.31],
            "Восст. энергии": [4.53, 5.18, 5.83, 6.48],
            "Сила атаки": [13.62, 15.56, 17.51, 19.45],
            "Защита": [16.20, 18.52, 20.83, 23.15],
            "HP": [209.13, 239.00, 268.88, 298.75],
        },
        "substat_spawn_weights": {
            "HP": 6,
            "Сила атаки": 6,
            "Защита": 6,
            "HP %": 4,
            "Сила атаки %": 4,
            "Защита %": 4,
            "Мастерство стихий": 4,
            "Восст. энергии": 4,
            "Шанс крит. попадания": 3,
            "Крит. урон": 3,
        },
        "mainstat_slot_weights": {
            "Пески времени": {
                "HP %": 26.68,
                "Сила атаки %": 26.66,
                "Защита %": 26.66,
                "Восст. энергии": 10.0,
                "Мастерство стихий": 10.0,
            },
            "Кубок пространства": {
                "HP %": 19.25,
                "Сила атаки %": 19.25,
                "Защита %": 19.0,
                "Пиро урон %": 5.0,
                "Гидро урон %": 5.0,
                "Электро урон %": 5.0,
                "Крио урон %": 5.0,
                "Анемо урон %": 5.0,
                "Гео урон %": 5.0,
                "Дендро урон %": 5.0,
                "Физ. урон %": 5.0,
                "Мастерство стихий": 2.5,
            },
            "Корона разума": {
                "HP %": 22.0,
                "Сила атаки %": 22.0,
                "Защита %": 22.0,
                "Крит. урон": 10.0,
                "Шанс крит. попадания": 10.0,
                "Бонус лечения %": 10.0,
                "Мастерство стихий": 4.0,
            }
        },
        "roll_tier_probabilities": [0.25, 0.25, 0.25, 0.25]
    }

    with open(os.path.join(DATA_DIR, "relic_math.json"), "w", encoding="utf-8") as f:
        json.dump(relic_math, f, ensure_ascii=False, indent=2)

    print(f"✅ Sync complete! Generated:")
    print(f" - {len(chars_meta)} characters in characters_meta.json")
    print(f" - {len(artifacts_ru)} sets in artifacts_ru.json")
    print(f" - {len(builds_list)} meta-builds in builds.json")
    print(f" - relic_math.json with exact AnimeGameData probabilities")


if __name__ == "__main__":
    sync_all()
