from flask import Blueprint, jsonify, request
from src.models.note import Note, db
# import translate helper from llm
from src.llm import translate_to_language, extract_structured_notes

note_bp = Blueprint('note', __name__)

@note_bp.route('/notes', methods=['GET'])
def get_notes():
    """Get all notes, ordered by saved position (if present), fallback to updated_at desc"""
    from sqlalchemy import nulls_last, asc, desc
    notes = Note.query.order_by(nulls_last(asc(Note.position)), desc(Note.updated_at)).all()
    return jsonify([note.to_dict() for note in notes])

@note_bp.route('/notes', methods=['POST'])
def create_note():
    """Create a new note"""
    try:
        data = request.json
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Title and content are required'}), 400
        
        # handle optional fields: tags (list or comma string), event_date (YYYY-MM-DD), event_time (HH:MM:SS)
        tags = data.get('tags')
        if isinstance(tags, list):
            tags_value = ','.join([t.strip() for t in tags if t is not None])
        else:
            tags_value = tags or None

        event_date = None
        if data.get('event_date'):
            from datetime import date
            try:
                event_date = date.fromisoformat(data.get('event_date'))
            except Exception:
                return jsonify({'error': 'event_date must be in YYYY-MM-DD format'}), 400

        event_time = None
        if data.get('event_time'):
            from datetime import time
            try:
                event_time = time.fromisoformat(data.get('event_time'))
            except Exception:
                return jsonify({'error': 'event_time must be in HH:MM:SS format'}), 400

        note = Note(title=data['title'], content=data['content'], tags=tags_value, event_date=event_date, event_time=event_time)
        # assign position to end
        from sqlalchemy import func
        max_pos = db.session.query(func.max(Note.position)).scalar()
        note.position = (max_pos or 0) + 1
        db.session.add(note)
        db.session.commit()
        return jsonify(note.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Get a specific note by ID"""
    note = Note.query.get_or_404(note_id)
    return jsonify(note.to_dict())

@note_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """Update a specific note"""
    try:
        note = Note.query.get_or_404(note_id)
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        note.title = data.get('title', note.title)
        note.content = data.get('content', note.content)
        # tags
        if 'tags' in data:
            tags = data.get('tags')
            if isinstance(tags, list):
                note.tags = ','.join([t.strip() for t in tags if t is not None])
            else:
                note.tags = tags or None
        # event_date
        if 'event_date' in data:
            if data.get('event_date'):
                from datetime import date
                try:
                    note.event_date = date.fromisoformat(data.get('event_date'))
                except Exception:
                    return jsonify({'error': 'event_date must be in YYYY-MM-DD format'}), 400
            else:
                note.event_date = None
        # event_time
        if 'event_time' in data:
            if data.get('event_time'):
                from datetime import time
                try:
                    note.event_time = time.fromisoformat(data.get('event_time'))
                except Exception:
                    return jsonify({'error': 'event_time must be in HH:MM:SS format'}), 400
            else:
                note.event_time = None
        db.session.commit()
        return jsonify(note.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a specific note"""
    try:
        note = Note.query.get_or_404(note_id)
        db.session.delete(note)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/search', methods=['GET'])
def search_notes():
    """Search notes by title or content"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    # support searching by title/content and by tag via ?tag=tagname
    tag = request.args.get('tag')
    q = Note.query
    if query:
        q = q.filter((Note.title.contains(query)) | (Note.content.contains(query)))
    if tag:
        # simple contains on comma-separated tags
        q = q.filter(Note.tags.contains(tag))
    notes = q.order_by(Note.updated_at.desc()).all()
    
    return jsonify([note.to_dict() for note in notes])


@note_bp.route('/notes/reorder', methods=['POST'])
def reorder_notes():
    """Persist new order of notes. Expects JSON: { "order": [id1, id2, ...] }"""
    try:
        data = request.json or {}
        order = data.get('order')
        if not order or not isinstance(order, list):
            return jsonify({'error': 'order must be a list of note ids'}), 400

        # update positions
        for idx, note_id in enumerate(order, start=1):
            n = Note.query.get(note_id)
            if n:
                n.position = idx
        db.session.commit()
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@note_bp.route('/notes/<int:note_id>/translate', methods=['POST'])
def translate_note(note_id):
    """Translate a note's title and content into a target language using the project's LLM helper.
    Expects JSON: { "target_language": "Chinese" }
    Returns: { "title": "...", "content": "..." }
    """
    try:
        note = Note.query.get_or_404(note_id)
        data = request.json or {}
        target = data.get('target_language') or data.get('language') or 'English'

        # Translate title and content separately
        translated_title = ''
        translated_content = ''
        try:
            translated_title = translate_to_language(note.title or '', target) if (note.title or '').strip() else ''
        except Exception:
            translated_title = ''

        try:
            translated_content = translate_to_language(note.content or '', target) if (note.content or '').strip() else ''
        except Exception as e:
            # if content translation fails, include error message in response
            return jsonify({'error': f'Content translation failed: {str(e)}'}), 500

        return jsonify({'title': translated_title, 'content': translated_content}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@note_bp.route('/notes/generate', methods=['POST'])
def generate_note():
    """Generate a structured note from a natural language prompt using the LLM.
    Expects JSON: { "prompt": "meeting tomorrow 3pm", "language": "English" }
    Returns created note object.
    """
    try:
        data = request.json or {}
        user_prompt = data.get('prompt') or data.get('text') or ''
        lang = data.get('language') or data.get('lang') or 'English'

        if not user_prompt or not user_prompt.strip():
            return jsonify({'error': 'prompt is required'}), 400

        # call LLM to extract structured note
        llm_raw = extract_structured_notes(user_prompt, lang=lang)

        # try to parse JSON from LLM raw response
        import json, re
        parsed = None
        try:
            parsed = json.loads(llm_raw)
        except Exception:
            m = re.search(r"\{[\s\S]*\}", llm_raw)
            if m:
                try:
                    parsed = json.loads(m.group(0))
                except Exception:
                    parsed = None

        if not parsed:
            return jsonify({'error': 'LLM did not return valid JSON', 'raw': llm_raw}), 500

        # Extract fields with fallback keys
        title = parsed.get('Title') or parsed.get('title') or parsed.get('Title'.lower(), 'Untitled')
        content = parsed.get('Notes') or parsed.get('notes') or parsed.get('Notes'.lower(), '')
        tags = parsed.get('Tags') or parsed.get('tags') or []
        tags_value = None
        if isinstance(tags, list):
            tags_value = ','.join([t.strip() for t in tags if t])
        elif isinstance(tags, str):
            tags_value = tags

        # create and persist note
        from sqlalchemy import func
        max_pos = db.session.query(func.max(Note.position)).scalar()
        note = Note(title=title or 'Untitled', content=content or '', tags=tags_value)
        note.position = (max_pos or 0) + 1
        db.session.add(note)
        db.session.commit()

        return jsonify(note.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

