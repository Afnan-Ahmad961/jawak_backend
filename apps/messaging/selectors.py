"""Read-only queries for messaging."""

from django.db.models import Q

from apps.messaging.models import Conversation


def _base_qs():
    return Conversation.objects.select_related(
        'design_request', 'design_request__client', 'vendor', 'vendor__user'
    )


def conversations_for_user(*, user):
    return _base_qs().filter(
        Q(design_request__client=user) | Q(vendor__user=user)
    ).distinct()


def conversation_get(*, conversation_id):
    return _base_qs().get(id=conversation_id)


def conversation_is_participant(*, conversation, user):
    return (
        conversation.design_request.client_id == user.id
        or conversation.vendor.user_id == user.id
    )


def messages_for_conversation(*, conversation):
    return conversation.messages.select_related('sender').all()
