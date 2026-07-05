from django.urls import path

from apps.messaging.views import ConversationListCreateView, MessageListCreateView

app_name = 'messaging'

urlpatterns = [
    path('', ConversationListCreateView.as_view(), name='list-create'),
    path(
        '<int:conversation_id>/messages/',
        MessageListCreateView.as_view(),
        name='messages',
    ),
]
