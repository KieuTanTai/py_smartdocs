from rest_framework import serializers
from .models import ConversationModel, MessageModel, DocumentModel

class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationModel
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageModel
        fields = '__all__'

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentModel
        fields = '__all__'
