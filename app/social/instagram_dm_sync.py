import requests
from datetime import datetime
from flask import current_app

API_BASE = 'https://graph.facebook.com/v19.0'


def _get_token_and_business_id():
    token = current_app.config.get('INSTAGRAM_ACCESS_TOKEN')
    business_id = current_app.config.get('INSTAGRAM_BUSINESS_ACCOUNT_ID')
    if not token or not business_id:
        raise ValueError('Instagram credentials not configured (INSTAGRAM_ACCESS_TOKEN / INSTAGRAM_BUSINESS_ACCOUNT_ID).')
    return token, business_id


def _iter_paged(url, params=None, max_pages=50, timeout=20):
    """Iterate through Graph API pagination. Yields each response JSON."""
    pages = 0
    while url and pages < max_pages:
        resp = requests.get(url, params=params if pages == 0 else None, timeout=timeout)
        if resp.status_code >= 300:
            try:
                err = resp.json()
            except Exception:
                err = {'message': resp.text}
            raise RuntimeError(f'Graph API error (HTTP {resp.status_code}): {err}')

        data = resp.json()
        yield data

        paging = data.get('paging') or {}
        url = paging.get('next')
        params = None
        pages += 1


def fetch_instagram_conversations(limit=50):
    """Fetch conversation/thread list.

    NOTE: Graph API capabilities vary by account type/app review.
    We try a couple of endpoints used in Meta messaging APIs.
    """
    token, business_id = _get_token_and_business_id()

    # Try business_id conversations first
    candidates = [
        (f"{API_BASE}/{business_id}/conversations", {
            'fields': 'id,updated_time,participants',
            'limit': str(limit),
            'access_token': token,
        }),
        # Fallback used by some messaging setups
        (f"{API_BASE}/me/conversations", {
            'fields': 'id,updated_time,participants',
            'limit': str(limit),
            'access_token': token,
        }),
    ]

    last_error = None
    for url, params in candidates:
        try:
            conversations = []
            for page in _iter_paged(url, params=params, max_pages=10):
                conversations.extend(page.get('data') or [])
            return conversations
        except Exception as e:
            last_error = e

    raise RuntimeError(f'Unable to fetch conversations from Graph API: {last_error}')


def fetch_conversation_messages(conversation_id, limit=50):
    """Fetch messages for a conversation/thread."""
    token, _ = _get_token_and_business_id()

    url = f"{API_BASE}/{conversation_id}/messages"
    params = {
        # Meta returns different shapes depending on product; request common fields.
        'fields': 'id,created_time,from,to,message',
        'limit': str(limit),
        'access_token': token,
    }

    messages = []
    for page in _iter_paged(url, params=params, max_pages=50):
        messages.extend(page.get('data') or [])

    return messages


def _parse_graph_dt(value):
    if not value:
        return None
    # Graph timestamps are usually ISO 8601 like 2020-01-01T00:00:00+0000
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            dt = datetime.strptime(value, fmt)
            # Store naive UTC in DB (existing code uses utcnow())
            return dt.astimezone(tz=None).replace(tzinfo=None)
        except Exception:
            continue
    try:
        # Try Python's parser for +00:00 style if present
        return datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=None)
    except Exception:
        return None


def sync_previous_instagram_dms(max_conversations=50, max_messages_per_conversation=50):
    """Pull recent conversations/messages from Instagram Graph API and upsert into DB.

    Returns summary dict.
    """
    from .. import db
    from ..models import DMConversation, DMMessage

    token, business_id = _get_token_and_business_id()

    conversations = fetch_instagram_conversations(limit=max_conversations)
    conversations = conversations[:max_conversations]

    created_conversations = 0
    created_messages = 0
    skipped_messages = 0

    for conv in conversations:
        conv_id = conv.get('id')
        if not conv_id:
            continue

        # Try to infer the other participant as "instagram_user_id".
        # If unavailable, fall back to a stable synthetic key.
        instagram_user_id = None
        instagram_username = None

        participants = (conv.get('participants') or {}).get('data') if isinstance(conv.get('participants'), dict) else None
        if isinstance(participants, list):
            for p in participants:
                pid = p.get('id')
                if pid and pid != business_id:
                    instagram_user_id = pid
                    instagram_username = p.get('username') or p.get('name')
                    break

        if not instagram_user_id:
            instagram_user_id = f"thread:{conv_id}"

        conversation = DMConversation.query.filter_by(instagram_user_id=instagram_user_id).first()
        if not conversation:
            conversation = DMConversation(
                instagram_user_id=instagram_user_id,
                instagram_username=instagram_username,
                platform='instagram',
                message_count=0,
                auto_reply_count=0,
            )
            db.session.add(conversation)
            db.session.flush()
            created_conversations += 1
        else:
            # Update username if we learned it
            if instagram_username and not conversation.instagram_username:
                conversation.instagram_username = instagram_username

        try:
            messages = fetch_conversation_messages(conv_id, limit=max_messages_per_conversation)
        except Exception as e:
            current_app.logger.error(f'Failed to fetch messages for conversation {conv_id}: {e}')
            continue

        # Oldest -> newest for nicer history
        messages.reverse()

        for m in messages:
            mid = m.get('id')
            text = m.get('message') or ''
            created_time = _parse_graph_dt(m.get('created_time'))
            sender = m.get('from') or {}
            sender_id = sender.get('id')

            if not (mid and text):
                continue

            # Avoid duplicates via unique instagram_message_id
            if DMMessage.query.filter_by(instagram_message_id=mid).first():
                skipped_messages += 1
                continue

            sender_type = 'user'
            if sender_id and sender_id == business_id:
                sender_type = 'bot'

            msg = DMMessage(
                conversation_id=conversation.id,
                instagram_message_id=mid,
                sender_type=sender_type,
                message_text=text,
                is_auto_reply=(sender_type == 'bot'),
                created_at=created_time or datetime.utcnow(),
            )
            db.session.add(msg)
            created_messages += 1

            # Update conversation fields
            conversation.last_message_at = msg.created_at
            conversation.message_count = (conversation.message_count or 0) + 1
            if sender_type == 'bot':
                conversation.auto_reply_count = (conversation.auto_reply_count or 0) + 1

        db.session.commit()

    return {
        'conversations_fetched': len(conversations),
        'conversations_created': created_conversations,
        'messages_created': created_messages,
        'messages_skipped_existing': skipped_messages,
    }
