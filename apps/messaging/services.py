"""Write operations (business logic) for messaging."""

from django.core.exceptions import ValidationError

from apps.messaging.models import Conversation, Message


def conversation_start(*, user, design_request, vendor):
    """Get or create the thread between a request's client and a vendor.

    The caller must be one of the two participants (the request's client or
    the vendor's user).
    """
    is_client = design_request.client_id == user.id
    is_vendor = vendor.user_id == user.id
    if not (is_client or is_vendor):
        raise ValidationError('You are not a participant of this conversation.')

    conversation, _ = Conversation.objects.get_or_create(
        design_request=design_request, vendor=vendor
    )
    return conversation


def message_send(*, conversation, sender, body):
    message = Message(conversation=conversation, sender=sender, body=body)
    message.full_clean()
    message.save()
    # Bump the conversation so it sorts to the top of each inbox.
    conversation.save(update_fields=['updated_at'])

    client = conversation.design_request.client
    vendor_user = conversation.vendor.user
    recipient = vendor_user if sender.id == client.id else client

    from apps.notifications.services import notify

    notify(
        recipient=recipient,
        notification_type='new_message',
        message=f'New message on "{conversation.design_request.title}".',
        target=conversation,
    )
    return message
