"""Adapter module for Genshin Open Object Data (GOOD) specification.

Provides bidirectional translation between standard GOOD keys and internal
Russian artifact nomenclature, with strict Decimal numeric precision.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping, Sequence

D = Decimal


class GoodFormatError(ValueError):
    """Raised when GOOD payload is malformed or contains unrecognized structures."""


SLOT_TO_GOOD: dict[str, str] = {
    "Цветок жизни": "flower",
    "Перо смерти": "plume",
    "Пески времени": "sands",
    "Кубок пространства": "goblet",
    "Корона проницательности": "circlet",
}
SLOT_FROM_GOOD: dict[str, str] = {v: k for k, v in SLOT_TO_GOOD.items()}


STAT_TO_GOOD: dict[str, str] = {
    "HP": "hp",
    "HP %": "hp_",
    "Сила атаки": "atk",
    "Сила атаки %": "atk_",
    "Защита": "def",
    "Защита %": "def_",
    "Мастерство стихий": "eleMas",
    "Восст. энергии": "enerRech_",
    "Шанс крит. попадания": "critRate_",
    "Крит. урон": "critDMG_",
    "Бонус лечения": "heal_",
    "Физ. урон %": "physical_dmg_",
    "Пиро урон %": "pyro_dmg_",
    "Гидро урон %": "hydro_dmg_",
    "Крио урон %": "cryo_dmg_",
    "Электро урон %": "electro_dmg_",
    "Анемо урон %": "anemo_dmg_",
    "Гео урон %": "geo_dmg_",
    "Дендро урон %": "dendro_dmg_",
}
STAT_FROM_GOOD: dict[str, str] = {v: k for k, v in STAT_TO_GOOD.items()}


@dataclass(frozen=True)
class ParsedArtifact:
    slot: str
    main_stat: str
    level: int
    rarity: int
    substats: list[tuple[str, Decimal]]
    set_key: str = ""
    location: str = ""
    lock: bool = False


def slot_good_to_internal(good_key: str) -> str:
    key = good_key.strip().lower()
    if key not in SLOT_FROM_GOOD:
        raise GoodFormatError(f"Unrecognized GOOD slotKey: {good_key}")
    return SLOT_FROM_GOOD[key]


def slot_internal_to_good(internal_name: str) -> str:
    name = internal_name.strip()
    if name == "Корона разума":
        return "circlet"
    if name not in SLOT_TO_GOOD:
        raise GoodFormatError(f"Unrecognized internal slot: {internal_name}")
    return SLOT_TO_GOOD[name]


def stat_good_to_internal(good_key: str) -> str:
    key = good_key.strip()
    # Normalize case-insensitively while preserving trailing underscore
    normalized = key.lower()
    for gk, ik in STAT_FROM_GOOD.items():
        if gk.lower() == normalized:
            return ik
    raise GoodFormatError(f"Unrecognized GOOD statKey: {good_key}")


def stat_internal_to_good(internal_name: str) -> str:
    name = internal_name.strip()
    if name not in STAT_TO_GOOD:
        raise GoodFormatError(f"Unrecognized internal stat: {internal_name}")
    return STAT_TO_GOOD[name]


def to_good_artifact(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Converts internal artifact dictionary into standard GOOD artifact dictionary."""
    slot_raw = artifact.get("slot", "")
    main_stat_raw = artifact.get("main_stat", "")

    slot_key = slot_internal_to_good(str(slot_raw))
    main_stat_key = stat_internal_to_good(str(main_stat_raw))

    substats_out = []
    for sub in artifact.get("substats", []):
        if isinstance(sub, dict):
            stat_name = sub.get("stat") or sub.get("key", "")
            val = sub.get("value", 0)
        elif isinstance(sub, (list, tuple)) and len(sub) == 2:
            stat_name, val = sub
        else:
            continue

        if not stat_name:
            continue
        good_sub_key = stat_internal_to_good(str(stat_name))
        float_val = float(D(str(val)))
        substats_out.append({"key": good_sub_key, "value": float_val})

    level = int(artifact.get("level", 0))
    rarity = int(artifact.get("rarity", 5))
    set_key = str(artifact.get("set_key") or artifact.get("setKey") or "GladiatorsFinale")

    return {
        "setKey": set_key,
        "slotKey": slot_key,
        "rarity": rarity,
        "mainStatKey": main_stat_key,
        "level": level,
        "substats": substats_out,
        "location": str(artifact.get("location", "")),
        "lock": bool(artifact.get("lock", False)),
    }


def to_good_json(artifacts: Sequence[Mapping[str, Any]] | Mapping[str, Any], indent: int = 2) -> str:
    """Serializes a single artifact or collection of artifacts into a GOOD JSON string."""
    if isinstance(artifacts, Sequence) and not isinstance(artifacts, (str, bytes)):
        good_artifacts = [to_good_artifact(a) for a in artifacts]
    else:
        good_artifacts = [to_good_artifact(artifacts)]

    payload = {
        "format": "GOOD",
        "version": 2,
        "source": "Genshin Artifact Calculator v2",
        "artifacts": good_artifacts,
    }
    return json.dumps(payload, indent=indent, ensure_ascii=False)


def from_good_artifact(data: Mapping[str, Any]) -> ParsedArtifact:
    """Parses a single GOOD artifact dictionary into a ParsedArtifact dataclass."""
    if not isinstance(data, Mapping):
        raise GoodFormatError("Artifact payload must be a JSON object mapping.")

    slot_key = data.get("slotKey")
    main_stat_key = data.get("mainStatKey")
    if not slot_key or not main_stat_key:
        raise GoodFormatError("Missing required GOOD fields: 'slotKey' or 'mainStatKey'.")

    internal_slot = slot_good_to_internal(str(slot_key))
    internal_main = stat_good_to_internal(str(main_stat_key))
    level = int(data.get("level", 0))
    rarity = int(data.get("rarity", 5))
    set_key = str(data.get("setKey", ""))
    location = str(data.get("location", ""))
    lock = bool(data.get("lock", False))

    substats: list[tuple[str, Decimal]] = []
    raw_substats = data.get("substats", [])
    if isinstance(raw_substats, Sequence):
        for item in raw_substats:
            if isinstance(item, Mapping) and "key" in item and "value" in item:
                s_name = stat_good_to_internal(str(item["key"]))
                s_val = D(str(item["value"]))
                substats.append((s_name, s_val))

    return ParsedArtifact(
        slot=internal_slot,
        main_stat=internal_main,
        level=level,
        rarity=rarity,
        substats=substats,
        set_key=set_key,
        location=location,
        lock=lock,
    )


def from_good_json(json_str: str) -> list[ParsedArtifact]:
    """Parses a GOOD JSON string (single artifact or root collection) into ParsedArtifact objects."""
    clean_str = json_str.strip()
    if not clean_str:
        raise GoodFormatError("Empty input provided for GOOD JSON.")

    try:
        data = json.loads(clean_str)
    except json.JSONDecodeError as err:
        raise GoodFormatError(f"Invalid JSON syntax: {err}") from err

    if isinstance(data, Mapping):
        if "artifacts" in data and isinstance(data["artifacts"], Sequence):
            return [from_good_artifact(item) for item in data["artifacts"] if isinstance(item, Mapping)]
        return [from_good_artifact(data)]
    elif isinstance(data, Sequence):
        return [from_good_artifact(item) for item in data if isinstance(item, Mapping)]

    raise GoodFormatError("Unrecognized GOOD JSON root structure.")
