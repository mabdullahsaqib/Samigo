from datetime import datetime
import google.generativeai as genai
from firebase_admin import firestore
from flask import jsonify, request
from .config import GEMINI_API_KEY
from .firebase_initializer import db

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


def get_next_note_id():
    """Retrieve and increment the note ID from a Firestore counter."""
    counter_ref = db.collection("metadata").document("note_counter")
    counter_doc = counter_ref.get()
    current_id = counter_doc.to_dict().get("count", 0) if counter_doc.exists else 0
    next_id = current_id + 1
    counter_ref.set({"count": next_id})
    return next_id


def add_note(title, content, tags=None):
    """Add a note to Firestore."""
    try:
        note_id = get_next_note_id()
        note_ref = db.collection("notes").document(str(note_id))
        note_data = {
            "note_id": note_id,
            "title": title,
            "content": content,
            "timestamp": datetime.now(),
            "tags": tags or []
        }
        note_ref.set(note_data)
        return {"message": "Note added successfully!", "note_id": note_id}
    except Exception as e:
        return {"error": str(e)}


def retrieve_notes(note_id=None, keyword=None, tag=None, date_range=None):
    """Retrieve notes from Firestore based on criteria."""
    try:
        query = db.collection("notes")
        if note_id:
            query = query.where("note_id", "==", note_id)
            return {"notes": [note.to_dict() for note in query.stream()]}

        if tag:
            query = query.where("tags", "array_contains", tag)
        if date_range:
            start_date, end_date = date_range
            query = query.where("timestamp", ">=", start_date).where("timestamp", "<=", end_date)

        notes = [note.to_dict() for note in query.stream()]

        if keyword:
            notes = [note for note in notes if keyword.lower() in note["content"].lower()]

        return {"notes": notes}
    except Exception as e:
        return {"error": str(e)}


def summarize_note(note_id):
    """Summarize the content of a note using Gemini."""
    try:
        note = db.collection("notes").document(note_id).get()
        if not note.exists:
            return {"error": "Note not found."}

        content = note.to_dict()["content"]
        summary = model.generate_content("Summarize the following text: " + content).text
        return {"summary": summary}
    except Exception as e:
        return {"error": str(e)}


def delete_note(note_id):
    """Delete a note by its ID."""
    try:
        db.collection("notes").document(note_id).delete()
        return {"message": "Note deleted successfully!"}
    except Exception as e:
        return {"error": str(e)}


def edit_note(note_id, new_title=None, new_content=None, new_tags=None):
    """Edit a note's title, content, or tags."""
    try:
        note_ref = db.collection("notes").document(note_id)
        update_data = {}
        if new_title:
            update_data["title"] = new_title
        if new_content:
            update_data["content"] = new_content
        if new_tags is not None:
            update_data["tags"] = new_tags

        note_ref.update(update_data)
        return {"message": "Note updated successfully!"}
    except Exception as e:
        return {"error": str(e)}


def note_voice_interaction(data):
    """
    Handle note-related requests.
    Supports add, retrieve, summarize, delete, and edit actions.

    Request Format:
        {
            "action": "add/retrieve/summarize/delete/edit",
            "payload": {
                // parameters depending on the action
            }
        }
    """

    action = data.get("command", "")
    payload = data.get("payload", {})

    if action == "add":
        return add_note(payload.get("title"), payload.get("content"), payload.get("tags"))

    elif action == "retrieve":
        return jsonify(retrieve_notes(
            note_id=payload.get("note_id"),
            keyword=payload.get("keyword"),
            tag=payload.get("tag"),
            date_range=payload.get("date_range"),
        ))

    elif action == "summarize":
        return summarize_note(payload.get("note_id"))

    elif action == "delete":
        return delete_note(payload.get("note_id"))

    elif action == "edit":
        return edit_note(
            note_id=payload.get("note_id"),
            new_title=payload.get("new_title"),
            new_content=payload.get("new_content"),
            new_tags=payload.get("new_tags"),
        )

    else:
        return {"error": "Invalid action specified."}