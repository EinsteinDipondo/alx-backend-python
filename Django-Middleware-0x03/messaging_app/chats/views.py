from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_list(request):
    return Response({"message": "Conversation list"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def message_list(request):
    return Response({"message": "Message list"})

@api_view(['GET'])
def test_view(request):
    return Response({"message": "Test endpoint for logging"})