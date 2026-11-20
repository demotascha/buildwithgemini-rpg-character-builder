#!/usr/bin/env python3
"""Seed script for populating characters in Firestore."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-bd1aa8bc4539"

SAMPLE_CHARACTERS = [
    {
        "id": "char-eldrin",
        "name": "Eldrin Swiftwind",
        "race": "Elf",
        "character_class": "Ranger",
        "level": 3,
        "background": "Outlander",
        "alignment": "Chaotic Good",
        "stats": {
            "strength": 12,
            "dexterity": 17,
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 15,
            "charisma": 8,
        },
        "hp": 28,
        "equipment": ["Longbow", "Quiver with 20 arrows", "Leather Armor", "Shortswords (x2)", "Hunting Trap"],
        "backstory": "A vigilant scout from the Whispering Woods protecting ancient borders against goblin raids.",
    },
    {
        "id": "char-morgran",
        "name": "Morgran Ironbreaker",
        "race": "Dwarf",
        "character_class": "Cleric",
        "level": 4,
        "background": "Acolyte",
        "alignment": "Lawful Good",
        "stats": {
            "strength": 16,
            "dexterity": 8,
            "constitution": 16,
            "intelligence": 12,
            "wisdom": 16,
            "charisma": 10,
        },
        "hp": 35,
        "equipment": ["Warhammer", "Chain Mail", "Shield with Holy Symbol", "Healer's Kit"],
        "backstory": "Devout follower of the Forge God, seeking lost relics of the ancient dwarven halls.",
    },
    {
        "id": "char-lyra",
        "name": "Lyra Shadowsong",
        "race": "Tiefling",
        "character_class": "Bard",
        "level": 3,
        "background": "Entertainer",
        "alignment": "Chaotic Neutral",
        "stats": {
            "strength": 8,
            "dexterity": 15,
            "constitution": 12,
            "intelligence": 13,
            "wisdom": 10,
            "charisma": 17,
        },
        "hp": 24,
        "equipment": ["Lute", "Rapier", "Leather Armor", "Disguise Kit", "Fine Clothes"],
        "backstory": "Wandering storyteller who collects forgotten legends and tavern gossip across kingdoms.",
    },
]


def seed_database():
    db = firestore.Client(project=PROJECT_ID)
    print(f"Connected to Firestore project: {PROJECT_ID}")
    collection_ref = db.collection("characters")

    for char in SAMPLE_CHARACTERS:
        doc_id = char["id"]
        collection_ref.document(doc_id).set(char)
        print(f"Seeded character: {char['name']} ({doc_id})")

    print(f"Successfully seeded {len(SAMPLE_CHARACTERS)} characters into 'characters' collection.")


if __name__ == "__main__":
    seed_database()
