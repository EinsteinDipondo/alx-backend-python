from rest_framework import serializers
from .models import User, Conversation, Message, ConversationParticipant


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'user_id',
            'first_name',
            'last_name',
            'email',
            'password',
            'confirm_password',
            'phone_number',
            'role',
            'created_at'
        ]
        read_only_fields = ['user_id', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_email(self, value):
        """Validate email uniqueness"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, data):
        """Validate password confirmation"""
        if 'password' in data and 'confirm_password' in data:
            if data['password'] != data['confirm_password']:
                raise serializers.ValidationError({
                    "confirm_password": "Passwords do not match."
                })
        return data

    def create(self, validated_data):
        """Create and return a new user with encrypted password"""
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        """Update and return an existing user instance"""
        validated_data.pop('confirm_password', None)
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
    message_body = serializers.CharField(
        required=True,
        max_length=1000,
        error_messages={
            'blank': 'Message body cannot be blank.',
            'max_length': 'Message body cannot exceed 1000 characters.'
        }
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

    def validate_message_body(self, value):
        """Validate message body"""
        if not value.strip():
            raise serializers.ValidationError("Message body cannot be empty.")
        return value.strip()


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
    title = serializers.CharField(
        required=False,
        max_length=100,
        allow_blank=True
    )

    class Meta:
        model = Conversation
        fields = [
            'conversation_id',
            'participants',
            'participant_ids',
            'messages',
            'conversation_participants',
            'title',
            'created_at'
        ]
        read_only_fields = ['conversation_id', 'created_at']

    def validate_participant_ids(self, value):
        """Validate participants"""
        if len(value) < 2:
            raise serializers.ValidationError(
                "A conversation must have at least 2 participants."
            )
        
        # Check for duplicate participants
        participant_ids = [user.user_id for user in value]
        if len(participant_ids) != len(set(participant_ids)):
            raise serializers.ValidationError(
                "Duplicate participants are not allowed."
            )
        
        return value

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
    recent_messages = serializers.SerializerMethodField()

    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ['recent_messages', 'messages']

    def get_recent_messages(self, obj):
        """Get recent messages (last 10)"""
        recent_messages = obj.messages.all().order_by('-sent_at')[:10]
        return MessageSerializer(recent_messages, many=True).data


class UserWithConversationsSerializer(UserSerializer):
    """
    User serializer with nested conversations
    """
    conversations = ConversationSerializer(many=True, read_only=True)
    unread_message_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['conversations', 'unread_message_count']

    def get_unread_message_count(self, obj):
        """Get count of unread messages for the user"""
        # This is a placeholder - you would implement actual unread message tracking
        return 0


class MessageWithConversationSerializer(MessageSerializer):
    """
    Message serializer with nested conversation details
    """
    conversation_details = serializers.SerializerMethodField()
    conversation_title = serializers.CharField(
        source='conversation.title',
        read_only=True
    )

    class Meta(MessageSerializer.Meta):
        fields = MessageSerializer.Meta.fields + ['conversation_details', 'conversation_title']

    def get_conversation_details(self, obj):
        """Get basic conversation details"""
        return {
            'conversation_id': obj.conversation.conversation_id,
            'created_at': obj.conversation.created_at,
            'participant_count': obj.conversation.participants.count(),
            'participant_names': [
                f"{user.first_name} {user.last_name}" 
                for user in obj.conversation.participants.all()
            ]
        }


class ConversationMessageSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for messages within a conversation context
    """
    sender_name = serializers.CharField(
        source='sender.get_full_name',
        read_only=True
    )
    sender_email = serializers.CharField(
        source='sender.email',
        read_only=True
    )
    formatted_sent_at = serializers.CharField(
        source='sent_at.strftime',
        read_only=True,
        default=lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if x else None
    )

    class Meta:
        model = Message
        fields = [
            'message_id',
            'sender_name',
            'sender_email',
            'message_body',
            'sent_at',
            'formatted_sent_at'
        ]
        read_only_fields = ['message_id', 'sent_at']