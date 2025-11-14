from rest_framework import serializers
from .models import User, Conversation, Message, ConversationParticipant


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model
    """
    class Meta:
        model = User
        fields = [
            'user_id',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'role',
            'created_at'
        ]
        read_only_fields = ['user_id', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        """Create and return a new user with encrypted password"""
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        """Update and return an existing user instance"""
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Message model
    """
    sender = UserSerializer(read_only=True)
    sender_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='sender',
        write_only=True
    )

    class Meta:
        model = Message
        fields = [
            'message_id',
            'sender',
            'sender_id',
            'conversation',
            'message_body',
            'sent_at'
        ]
        read_only_fields = ['message_id', 'sent_at']


class ConversationParticipantSerializer(serializers.ModelSerializer):
    """
    Serializer for ConversationParticipant through model
    """
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )

    class Meta:
        model = ConversationParticipant
        fields = ['user', 'user_id', 'joined_at']
        read_only_fields = ['joined_at']


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for Conversation model with nested relationships
    """
    participants = UserSerializer(many=True, read_only=True)
    participant_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='participants',
        many=True,
        write_only=True
    )
    messages = MessageSerializer(many=True, read_only=True)
    conversation_participants = ConversationParticipantSerializer(
        many=True, 
        read_only=True
    )

    class Meta:
        model = Conversation
        fields = [
            'conversation_id',
            'participants',
            'participant_ids',
            'messages',
            'conversation_participants',
            'created_at'
        ]
        read_only_fields = ['conversation_id', 'created_at']

    def create(self, validated_data):
        """
        Create conversation and add participants
        """
        participants = validated_data.pop('participants', [])
        conversation = Conversation.objects.create(**validated_data)
        
        # Add participants to the conversation
        for participant in participants:
            ConversationParticipant.objects.create(
                conversation=conversation,
                user=participant
            )
        
        return conversation

    def update(self, instance, validated_data):
        """
        Update conversation and handle participants
        """
        participants = validated_data.pop('participants', None)
        
        # Update conversation fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update participants if provided
        if participants is not None:
            # Clear existing participants
            instance.participants.clear()
            # Add new participants
            for participant in participants:
                ConversationParticipant.objects.create(
                    conversation=instance,
                    user=participant
                )
        
        return instance


class ConversationDetailSerializer(ConversationSerializer):
    """
    Detailed conversation serializer with full message history
    """
    messages = MessageSerializer(many=True, read_only=True)

    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ['messages']


class UserWithConversationsSerializer(UserSerializer):
    """
    User serializer with nested conversations
    """
    conversations = ConversationSerializer(many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['conversations']


class MessageWithConversationSerializer(MessageSerializer):
    """
    Message serializer with nested conversation details
    """
    conversation_details = serializers.SerializerMethodField()

    class Meta(MessageSerializer.Meta):
        fields = MessageSerializer.Meta.fields + ['conversation_details']

    def get_conversation_details(self, obj):
        """Get basic conversation details"""
        return {
            'conversation_id': obj.conversation.conversation_id,
            'created_at': obj.conversation.created_at,
            'participant_count': obj.conversation.participants.count()
        }