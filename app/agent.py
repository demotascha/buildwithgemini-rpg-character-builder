# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from .a2ui_utils import a2ui_callback


import dotenv

dotenv.load_dotenv()

MODEL = "gemini-3.8-flash"


import json
import uuid
from typing import Any, Dict, List, Optional
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-bd1aa8bc4539"


def _get_firestore_client() -> firestore.Client:
    return firestore.Client(project=PROJECT_ID)


def list_characters(limit: int = 10) -> str:
    """Lists characters stored in the RPG database.

    Args:
        limit: The maximum number of characters to retrieve (default 10).

    Returns:
        A JSON string containing the list of characters with their details.
    """
    db = _get_firestore_client()
    docs = db.collection("characters").limit(limit).stream()
    characters = [doc.to_dict() for doc in docs]
    return json.dumps(characters, ensure_ascii=False, indent=2)


def get_character(character_id_or_name: str) -> str:
    """Gets details for a specific character by ID or by name.

    Args:
        character_id_or_name: The ID (e.g. 'char-eldrin') or name of the character.

    Returns:
        A JSON string containing the character details, or an error message if not found.
    """
    db = _get_firestore_client()
    col = db.collection("characters")

    # Try direct ID lookup first
    doc = col.document(character_id_or_name).get()
    if doc.exists:
        return json.dumps(doc.to_dict(), ensure_ascii=False, indent=2)

    # Search by name (case-insensitive query scan)
    all_docs = col.stream()
    for d in all_docs:
        data = d.to_dict()
        if data.get("name", "").lower() == character_id_or_name.lower():
            return json.dumps(data, ensure_ascii=False, indent=2)

    return f"Character '{character_id_or_name}' not found."


def save_character(
    name: str,
    race: str,
    character_class: str,
    level: int = 1,
    background: str = "",
    alignment: str = "",
    strength: int = 10,
    dexterity: int = 10,
    constitution: int = 10,
    intelligence: int = 10,
    wisdom: int = 10,
    charisma: int = 10,
    hp: int = 10,
    equipment: Optional[List[str]] = None,
    backstory: str = "",
    character_id: Optional[str] = None,
) -> str:
    """Creates or updates a character in the Firestore database.

    Args:
        name: The character's name.
        race: The character's race (e.g. Elf, Dwarf, Human, Tiefling).
        character_class: The character's class (e.g. Ranger, Cleric, Bard, Wizard).
        level: Current character level (default 1).
        background: Character background (e.g. Outlander, Acolyte).
        alignment: Character alignment (e.g. Chaotic Good, Lawful Neutral).
        strength: Strength attribute (1-20).
        dexterity: Dexterity attribute (1-20).
        constitution: Constitution attribute (1-20).
        intelligence: Intelligence attribute (1-20).
        wisdom: Wisdom attribute (1-20).
        charisma: Charisma attribute (1-20).
        hp: Hit points.
        equipment: List of starting equipment/items.
        backstory: Brief character backstory and lore.
        character_id: Optional existing ID to update. If omitted, a new ID is generated.

    Returns:
        A confirmation message with the character ID and details.
    """
    db = _get_firestore_client()
    doc_id = character_id or f"char-{uuid.uuid4().hex[:8]}"

    character_data = {
        "id": doc_id,
        "name": name,
        "race": race,
        "character_class": character_class,
        "level": level,
        "background": background,
        "alignment": alignment,
        "stats": {
            "strength": strength,
            "dexterity": dexterity,
            "constitution": constitution,
            "intelligence": intelligence,
            "wisdom": wisdom,
            "charisma": charisma,
        },
        "hp": hp,
        "equipment": equipment or [],
        "backstory": backstory,
    }

    db.collection("characters").document(doc_id).set(character_data)
    return f"Successfully saved character '{name}' with ID '{doc_id}'."


def delete_character(character_id: str) -> str:
    """Deletes a character from the database by ID.

    Args:
        character_id: The ID of the character to delete.

    Returns:
        A confirmation message.
    """
    db = _get_firestore_client()
    doc_ref = db.collection("characters").document(character_id)
    if not doc_ref.get().exists:
        return f"Character with ID '{character_id}' does not exist."
    doc_ref.delete()
    return f"Successfully deleted character with ID '{character_id}'."


def roll_dice(expression: str) -> str:
    """Simulates rolling tabletop RPG dice (e.g., '1d20', '3d6+2', '1d20-1', '4d6').

    Args:
        expression: Dice notation string, such as '1d20', '2d6+3', '1d100', '4d6'.

    Returns:
        A string detailing each individual die roll and the final total.
    """
    import random
    import re

    clean_expr = expression.replace(" ", "").lower()
    pattern = r"^(\d+)d(\d+)([+-]\d+)?$"
    match = re.match(pattern, clean_expr)
    if not match:
        return f"Invalid dice expression '{expression}'. Please use format like '1d20', '2d6+3', or '3d8-1'."

    count, sides, modifier = int(match.group(1)), int(match.group(2)), match.group(3)
    if count < 1 or count > 50 or sides < 2 or sides > 1000:
        return "Dice count must be between 1 and 50, and sides must be between 2 and 1000."

    rolls = [random.randint(1, sides) for _ in range(count)]
    mod_val = int(modifier) if modifier else 0
    total = sum(rolls) + mod_val
    mod_str = f" {modifier}" if modifier else ""
    return f"Rolled {expression}: {rolls}{mod_str} = Total: {total}"


def lookup_dnd_spell(spell_name: str) -> str:
    """Looks up official 5th Edition D&D spell details from the public D&D 5e SRD API.

    Args:
        spell_name: The name of the spell to look up (e.g., 'Fireball', 'Mage Armor', 'Healing Word').

    Returns:
        A JSON string containing the spell's level, casting time, range, duration, components, and description.
    """
    import urllib.parse
    import urllib.request

    formatted_index = spell_name.lower().strip().replace(" ", "-").replace("'", "")
    # Try direct endpoint first
    url = f"https://www.dnd5eapi.co/api/2014/spells/{formatted_index}"
    req = urllib.request.Request(url, headers={"User-Agent": "RPG-Character-Builder/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            result = {
                "name": data.get("name"),
                "level": data.get("level"),
                "school": data.get("school", {}).get("name"),
                "casting_time": data.get("casting_time"),
                "range": data.get("range"),
                "duration": data.get("duration"),
                "components": data.get("components"),
                "description": " ".join(data.get("desc", [])),
                "higher_level": " ".join(data.get("higher_level", [])),
            }
            return json.dumps(result, ensure_ascii=False, indent=2)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Try search query endpoint to find closest matching spells
            search_url = f"https://www.dnd5eapi.co/api/2014/spells?name={urllib.parse.quote(spell_name)}"
            search_req = urllib.request.Request(search_url, headers={"User-Agent": "RPG-Character-Builder/1.0"})
            try:
                with urllib.request.urlopen(search_req, timeout=5) as search_resp:
                    search_data = json.loads(search_resp.read().decode("utf-8"))
                    results = search_data.get("results", [])
                    if results:
                        names = [r.get("name") for r in results]
                        return f"Spell '{spell_name}' not found directly. Did you mean one of these? {', '.join(names)}"
            except Exception:
                pass
            return f"Spell '{spell_name}' not found in D&D 5e SRD rules."
    except Exception as e:
        return f"Error querying D&D 5e API: {str(e)}"


def geocode_address(address: str) -> str:
    """Converts a street address, city, or landmark into latitude and longitude coordinates using the Google Maps Geocoding API.

    Args:
        address: The address or place name to geocode (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA').

    Returns:
        A JSON string containing the formatted address and location coordinates (latitude, longitude).
    """
    import os
    import urllib.parse
    import urllib.request

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY is not configured in the environment."

    encoded_addr = urllib.parse.quote(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_addr}&key={api_key}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") != "OK" or not data.get("results"):
                return f"Geocoding failed for address '{address}': {data.get('status', 'No results')}"

            first = data["results"][0]
            loc = first.get("geometry", {}).get("location", {})
            return json.dumps({
                "formatted_address": first.get("formatted_address"),
                "latitude": loc.get("lat"),
                "longitude": loc.get("lng"),
            }, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error calling Geocoding API: {str(e)}"


def find_nearby_places(latitude: float, longitude: float, place_type: str = "book_store", radius_meters: float = 5000.0) -> str:
    """Finds nearby places of a specific type using the Google Maps Places API (New).

    Args:
        latitude: The center latitude for the search.
        longitude: The center longitude for the search.
        place_type: The place type (e.g., 'book_store', 'cafe', 'park', 'lodging', 'restaurant').
        radius_meters: Search radius in meters (default 5000.0, max 50000.0).

    Returns:
        A JSON string containing key fields (name, address, location) for nearby places.
    """
    import os
    import urllib.request

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY is not configured in the environment."

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }

    body = json.dumps({
        "includedTypes": [place_type],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "radius": float(radius_meters),
            }
        },
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            places_list = []
            for p in data.get("places", []):
                places_list.append({
                    "name": p.get("displayName", {}).get("text"),
                    "address": p.get("formattedAddress"),
                    "location": p.get("location"),
                })
            return json.dumps(places_list, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error calling Places API (New): {str(e)}"


BUCKET_NAME = "rpg-portraits-qwiklabs-gcp-03-bd1aa8bc4539"


async def generate_item_image(item_name: str, description: str, tool_context: Any = None) -> str:
    """Generates a fantasy item or character concept image using the gemini-3.1-flash-lite-image model.

    Saves the image as a session artifact for the Playground's Artifacts panel, and uploads it to
    the public Cloud Storage bucket, returning the public HTTPS URL.

    Args:
        item_name: The name of the item, weapon, armor, relic, or character to illustrate.
        description: A visual description of the item or character (style, colors, details).
        tool_context: Context provided by the ADK runtime containing save_artifact.

    Returns:
        A JSON string containing the public Cloud Storage image URL and artifact status.
    """
    from google import genai
    from google.cloud import storage

    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global",
    )

    prompt = (
        f"A detailed fantasy tabletop RPG illustration of {item_name}: {description}. "
        "High quality, atmospheric concept art, centered view, transparent or clean background."
    )

    try:
        response = await client.aio.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
        )

        image_bytes = None
        mime_type = "image/jpeg"

        if response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/jpeg"
                    break

        if not image_bytes:
            return "Failed to generate image: No image data returned from model."

        # 1. Save artifact to ADK tool_context (shows in Playground Artifacts panel)
        artifact_filename = f"{item_name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:6]}.jpg"
        if tool_context and hasattr(tool_context, "save_artifact"):
            artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            await tool_context.save_artifact(
                filename=artifact_filename,
                artifact=artifact_part,
                custom_metadata={"item_name": item_name, "model": "gemini-3.1-flash-lite-image"},
            )

        # 2. Upload image bytes to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(artifact_filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{artifact_filename}"

        return json.dumps({
            "status": "success",
            "item_name": item_name,
            "artifact_saved": bool(tool_context and hasattr(tool_context, "save_artifact")),
            "artifact_filename": artifact_filename,
            "image_url": public_url,
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"Error generating or uploading item image: {str(e)}"


async def generate_item_video(item_name: str, description: str, tool_context: Any = None) -> str:
    """Generates a short showcase video for a fantasy RPG item, weapon, relic, or spell using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Saves the video as a session artifact with tool_context.save_artifact so it shows up
    in the Playground's Artifacts panel, and uploads the video bytes to the public Cloud Storage
    bucket (rpg-portraits-qwiklabs-gcp-03-bd1aa8bc4539), returning the public HTTPS URL.

    Args:
        item_name: The name of the fantasy item, weapon, artifact, or spell to animate.
        description: A visual motion description of the item (e.g. glowing runes, fire swirling, floating in darkness).
        tool_context: Context provided by the ADK runtime containing save_artifact.

    Returns:
        A JSON string containing the public Cloud Storage video URL, artifact status, and filename.
    """
    import base64
    from google import genai
    from google.cloud import storage

    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global",
    )

    prompt = (
        f"A short cinematic high fantasy showcase video of {item_name}: {description}. "
        "Smooth lighting, particle effects, 3D rotating cinematic close-up."
    )

    try:
        interaction = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
        )

        if not interaction.output_video or not interaction.output_video.data:
            return "Failed to generate video: No video data returned from model."

        video_bytes = base64.b64decode(interaction.output_video.data)
        mime_type = interaction.output_video.mime_type or "video/mp4"

        artifact_filename = f"{item_name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:6]}.mp4"

        # 1. Save artifact with tool_context.save_artifact (Playground Artifacts panel)
        if tool_context and hasattr(tool_context, "save_artifact"):
            artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
            await tool_context.save_artifact(
                filename=artifact_filename,
                artifact=artifact_part,
                custom_metadata={"item_name": item_name, "model": "gemini-omni-flash-preview"},
            )

        # 2. Upload video bytes to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket("rpg-portraits-qwiklabs-gcp-03-bd1aa8bc4539")
        blob = bucket.blob(artifact_filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/rpg-portraits-qwiklabs-gcp-03-bd1aa8bc4539/{artifact_filename}"

        return json.dumps({
            "status": "success",
            "item_name": item_name,
            "artifact_saved": bool(tool_context and hasattr(tool_context, "save_artifact")),
            "artifact_filename": artifact_filename,
            "video_url": public_url,
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"Error generating or uploading item video: {str(e)}"


SANDBOX_RESOURCE_NAME = "projects/264857547613/locations/us-central1/reasoningEngines/6383770283303501824/sandboxEnvironments/4246775976232484864"

sandbox_executor = AgentEngineSandboxCodeExecutor(
    sandbox_resource_name=SANDBOX_RESOURCE_NAME,
)


async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: after each turn, send the session events to Memory Bank for extraction."""
    await callback_context.add_session_to_memory()
    return None


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are an expert tabletop RPG character creation assistant and Lore Master. "
        "You help players design, view, and customize tabletop RPG characters and items. "
        "You remember the user's stated preferences, favorite character types, past campaign details, and rules from previous conversations and use them to personalize your responses. "
        "IMPORTANT: Always pay attention to and remember all user allergies, dietary restrictions, and medical/food sensitivities mentioned by the user. "
        "You have access to a database of saved characters via your tools. "
        "You can roll dice for character stats, checks, or combat using roll_dice. "
        "You can look up official D&D 5e spell rules using lookup_dnd_spell. "
        "You can generate high-quality fantasy illustrations for items, weapons, or characters using generate_item_image. "
        "You can geocode real-world locations using geocode_address and find nearby places using find_nearby_places. "
        "You can execute Python code in a safe Agent Engine sandbox environment to perform complex TRPG simulations, math, combat probability models, or loot table rolls. "
        "Whenever the user asks to see, create, find, or manage characters, roll dice, look up spells, generate images, search locations, or run Python calculations, use the appropriate tool."
    ),
    workflow_description="Analyze the request, call tools when needed, and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=sandbox_executor,
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        list_characters,
        get_character,
        save_character,
        delete_character,
        roll_dice,
        lookup_dnd_spell,
        generate_item_image,
        generate_item_video,
        geocode_address,
        find_nearby_places,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
