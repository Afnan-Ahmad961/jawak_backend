from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.design_requests.models import DesignRequest
from apps.messaging import selectors, services
from apps.messaging.models import Conversation
from apps.messaging.serializers import (
    ConversationSerializer,
    ConversationStartSerializer,
    MessageSerializer,
)
from apps.vendors.models import VendorProfile


class ConversationListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = selectors.conversations_for_user(user=request.user)
        return Response(ConversationSerializer(qs, many=True).data)

    def post(self, request):
        serializer = ConversationStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            design_request = DesignRequest.objects.get(
                id=serializer.validated_data['design_request']
            )
            vendor = VendorProfile.objects.get(
                id=serializer.validated_data['vendor']
            )
        except (DesignRequest.DoesNotExist, VendorProfile.DoesNotExist):
            raise Http404

        try:
            conversation = services.conversation_start(
                user=request.user, design_request=design_request, vendor=vendor
            )
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages)
        return Response(
            ConversationSerializer(conversation).data,
            status=status.HTTP_201_CREATED,
        )


class MessageListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _get_conversation(self, request, conversation_id):
        try:
            conversation = selectors.conversation_get(conversation_id=conversation_id)
        except Conversation.DoesNotExist:
            raise Http404
        if not selectors.conversation_is_participant(
            conversation=conversation, user=request.user
        ):
            raise PermissionDenied('You are not a participant of this conversation.')
        return conversation

    def get(self, request, conversation_id):
        conversation = self._get_conversation(request, conversation_id)
        messages = selectors.messages_for_conversation(conversation=conversation)
        return Response(MessageSerializer(messages, many=True).data)

    def post(self, request, conversation_id):
        conversation = self._get_conversation(request, conversation_id)
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            message = services.message_send(
                conversation=conversation,
                sender=request.user,
                body=serializer.validated_data['body'],
            )
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages)
        return Response(
            MessageSerializer(message).data, status=status.HTTP_201_CREATED
        )
