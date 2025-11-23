from __future__ import annotations

import glob
import json
import os
from typing import Any, Dict, List

from django.conf import settings
from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest, Http404
from django.views.decorators.http import require_GET, require_POST
from django.contrib.admin.views.decorators import staff_member_required

from constance import config as constance_config
from constance import settings as constance_settings
import polib


@staff_member_required
@require_GET
def translation_metadata(request: HttpRequest) -> JsonResponse:
    """Return basic translation metadata for each configured language.

    This inspects LOCALE_PATHS to find .po files for every LANGUAGE_CODE and
    returns a lightweight summary that the admin UI can render via AJAX.
    """

    languages: List[Dict[str, Any]] = []
    locale_paths = getattr(settings, "LOCALE_PATHS", [])

    for code, name in getattr(settings, "LANGUAGES", []):
        po_files: List[str] = []
        for base in locale_paths:
            pattern = os.path.join(str(base), code, "LC_MESSAGES", "*.po")
            po_files.extend(glob.glob(pattern))

        languages.append(
            {
                "code": code,
                "name": name,
                "po_count": len(po_files),
                "has_files": bool(po_files),
            }
        )

    return JsonResponse({"languages": languages})


def _serialize_constance_value(key: str, current: Any) -> Any:
    """Serialize values for JSON (handles non-JSON-native types conservatively)."""
    # For now, just return the value if it's JSON-serializable; otherwise str().
    try:
        json.dumps(current)
        return current
    except TypeError:
        return str(current)


@staff_member_required
@require_GET
def constance_settings_list(request: HttpRequest) -> JsonResponse:
    """Return CONSTANCE settings grouped by fieldsets for admin UI."""

    raw_config = constance_settings.CONFIG
    raw_fieldsets = getattr(constance_settings, "FIELDSETS", None)

    fieldsets_payload: List[Dict[str, Any]] = []

    if raw_fieldsets:
        fieldset_items = raw_fieldsets.items()
    else:
        # Fallback: single group with all keys
        fieldset_items = [("General", list(raw_config.keys()))]

    for set_name, keys in fieldset_items:
        items: List[Dict[str, Any]] = []
        for key in keys:
            if key not in raw_config:
                continue
            default, help_text, type_ = raw_config[key]
            current = getattr(constance_config, key)
            items.append(
                {
                    "key": key,
                    "help_text": help_text,
                    "type": getattr(type_, "__name__", str(type_)),
                    "default": _serialize_constance_value(key, default),
                    "value": _serialize_constance_value(key, current),
                }
            )

        fieldsets_payload.append({"name": set_name, "items": items})

    return JsonResponse({"fieldsets": fieldsets_payload})


@staff_member_required
@require_POST
def constance_settings_update(request: HttpRequest) -> JsonResponse:
    """Update CONSTANCE settings via JSON payload.

    Expected JSON body::

        {"updates": {"KEY": new_value, ...}}
    """

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return HttpResponseBadRequest("Invalid JSON body")

    updates: Dict[str, Any] = payload.get("updates") or {}
    if not isinstance(updates, dict):
        return HttpResponseBadRequest("'updates' must be an object")

    raw_config = constance_settings.CONFIG

    applied: Dict[str, Any] = {}
    errors: Dict[str, str] = {}

    for key, raw_value in updates.items():
        if key not in raw_config:
            errors[key] = "Unknown setting key"
            continue

        default, help_text, type_ = raw_config[key]

        try:
            if type_ is bool:
                # JSON booleans come through correctly; strings need coercion.
                if isinstance(raw_value, bool):
                    value = raw_value
                elif isinstance(raw_value, str):
                    value = raw_value.lower() in {"1", "true", "yes", "on"}
                else:
                    value = bool(raw_value)
            elif type_ is int:
                value = int(raw_value)
            elif type_ is float:
                value = float(raw_value)
            elif type_ is str:
                value = "" if raw_value is None else str(raw_value)
            else:
                # Fallback: store raw value
                value = raw_value

            setattr(constance_config, key, value)
            applied[key] = _serialize_constance_value(key, value)
        except (TypeError, ValueError) as exc:
            errors[key] = str(exc)

    return JsonResponse({"updated": applied, "errors": errors})


@staff_member_required
@require_GET
def chatbot_questions_list(request: HttpRequest) -> JsonResponse:
    """Return recent chatbot questions for display in the admin dashboard.

    This relies on the ChatbotQuestion model defined in shop.models.
    """

    from shop.models import ChatbotQuestion  # Imported here to avoid circular imports

    qs = ChatbotQuestion.objects.select_related("user").all()[:500]

    data: list[dict[str, Any]] = []
    for q in qs:
        data.append(
            {
                "id": q.id,
                "user": getattr(q.user, "email", None),
                "question": q.question,
                "answer": q.answer,
                "language_code": q.language_code,
                "source_path": q.source_path,
                "created_at": q.created_at.isoformat() if q.created_at else None,
            }
        )

    return JsonResponse({"questions": data})


@staff_member_required
@require_GET
def translation_messages(request: HttpRequest, lang_code: str) -> JsonResponse:
    """Return simple list of translation messages for a given language.

    This only exposes non-plural, non-obsolete entries from the first matching
    .po file under LOCALE_PATHS for the given language.
    """

    valid_codes = {code for code, _ in getattr(settings, "LANGUAGES", [])}
    if lang_code not in valid_codes:
        raise Http404("Unknown language code")

    locale_paths = getattr(settings, "LOCALE_PATHS", [])
    po_files: list[str] = []
    for base in locale_paths:
        pattern = os.path.join(str(base), lang_code, "LC_MESSAGES", "*.po")
        po_files.extend(glob.glob(pattern))

    if not po_files:
        return JsonResponse({"messages": [], "po_file": None})

    po_path = po_files[0]
    po = polib.pofile(po_path)

    messages_payload: list[dict[str, Any]] = []
    for entry in po:
        if entry.obsolete:
            continue
        if entry.msgid_plural:
            # Skip plural forms for this simplified UI
            continue
        if not (entry.msgid or "").strip():
            continue

        messages_payload.append(
            {
                "msgid": entry.msgid,
                "msgstr": entry.msgstr or "",
                "fuzzy": "fuzzy" in (entry.flags or []),
            }
        )

    return JsonResponse({"messages": messages_payload, "po_file": os.path.basename(po_path)})


@staff_member_required
@require_POST
def translation_messages_update(request: HttpRequest, lang_code: str) -> JsonResponse:
    """Update translation messages for a given language.

    Expected JSON body::

        {"messages": [{"msgid": "...", "msgstr": "..."}, ...]}
    """

    valid_codes = {code for code, _ in getattr(settings, "LANGUAGES", [])}
    if lang_code not in valid_codes:
        raise Http404("Unknown language code")

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return HttpResponseBadRequest("Invalid JSON body")

    messages_data = payload.get("messages") or []
    if not isinstance(messages_data, list):
        return HttpResponseBadRequest("'messages' must be a list")

    locale_paths = getattr(settings, "LOCALE_PATHS", [])
    po_files: list[str] = []
    for base in locale_paths:
        pattern = os.path.join(str(base), lang_code, "LC_MESSAGES", "*.po")
        po_files.extend(glob.glob(pattern))

    if not po_files:
        return JsonResponse({"updated": 0, "errors": {"_all": "No .po files found"}}, status=400)

    po_path = po_files[0]
    po = polib.pofile(po_path)

    entries_by_id: dict[str, polib.POEntry] = {}
    for entry in po:
        if entry.obsolete or entry.msgid_plural:
            continue
        if not (entry.msgid or "").strip():
            continue
        entries_by_id[entry.msgid] = entry

    updated_count = 0
    errors: dict[str, str] = {}

    for item in messages_data:
        msgid = item.get("msgid") if isinstance(item, dict) else None
        msgstr = item.get("msgstr", "") if isinstance(item, dict) else ""
        if not msgid:
            continue

        entry = entries_by_id.get(msgid)
        if not entry:
            errors[msgid] = "Message not found in PO file"
            continue

        if entry.msgid_plural:
            errors[msgid] = "Plural messages are not editable via this endpoint"
            continue

        if entry.msgstr != msgstr:
            entry.msgstr = msgstr
            if entry.flags and "fuzzy" in entry.flags:
                entry.flags.remove("fuzzy")
            updated_count += 1

    if updated_count:
        po.save()
        try:
            mo_path = os.path.splitext(po_path)[0] + ".mo"
            po.save_as_mofile(mo_path)
        except Exception as exc:  # pragma: no cover - best effort
            errors["_compile"] = str(exc)

    return JsonResponse({"updated": updated_count, "errors": errors})
