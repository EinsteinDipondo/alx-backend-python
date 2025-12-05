from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError

def health_check(request):
    """Health check endpoint for Docker"""
    try:
        # Check database connection
        connections['default'].cursor()
        db_status = 'healthy'
    except OperationalError:
        db_status = 'unhealthy'
    
    return JsonResponse({
        'status': 'ok',
        'database': db_status,
        'timestamp': time.time()
    })
