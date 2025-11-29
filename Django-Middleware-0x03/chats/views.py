# Add these views to your existing views.py file
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
def admin_dashboard(request):
    return Response({"message": "Admin dashboard - accessible only by admins"})

@api_view(['GET'])
def moderator_panel(request):
    return Response({"message": "Moderator panel - accessible by admins and moderators"})

@api_view(['GET'])
def user_management(request):
    return Response({"message": "User management - admin only"})

@api_view(['GET'])
def report_management(request):
    return Response({"message": "Report management - accessible by admins and moderators"})

@api_view(['POST'])
def bulk_delete_messages(request):
    return Response({"message": "Bulk delete messages - admin only"})