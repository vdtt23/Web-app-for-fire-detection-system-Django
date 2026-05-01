from django.shortcuts import render
from django.http import JsonResponse
from posts.models import SensorData
from django.utils import timezone

def home(request):
    return render(request, 'posts/home.html')


def dashboard(request):
    nodes = SensorData.objects.order_by('-created_at')[:10]

    fire_count = SensorData.objects.filter(status="FIRE").count()
    warning_count = SensorData.objects.filter(status="WARNING").count()

    return render(request, 'posts/dashboard.html', {
        'nodes': nodes,
        'fire_count': fire_count,
        'warning_count': warning_count
    })

def chart_data(request):
    qs = SensorData.objects.order_by('-created_at')[:20][::-1]  

    data = {
        "labels": [timezone.localtime(d.created_at).strftime("%H:%M:%S") for d in qs],
        "temp": [d.temperature for d in qs],
        "smoke": [d.smoke for d in qs],
        "humidity": [d.humidity for d in qs],
    }
    return JsonResponse(data)

def latest_nodes(request):
    qs = SensorData.objects.order_by('-created_at')[:10]
    data = [
        {
            "node_id": n.node_id,
            "temperature": n.temperature,
            "smoke": n.smoke,
            "humidity": n.humidity,
            "status": n.status,
        }
        for n in qs
    ]
    return JsonResponse(data, safe=False)

def alerts(request):
    alerts = SensorData.objects.filter(
        status__in=["FIRE", "WARNING"]
    ).order_by('-created_at')

    return render(request, 'posts/alerts.html', {
        'alerts': alerts
    })

def latest_alerts(request):
    qs = SensorData.objects.filter(
        status__in=["FIRE", "WARNING"]
    ).order_by('-created_at')[:10]

    data = [
        {
            "node_id": n.node_id,
            "temperature": n.temperature,
            "smoke": n.smoke,
            "humidity": n.humidity,
            "status": n.status,
        }
        for n in qs
    ]

    return JsonResponse(data, safe=False)

def about(request):
    return render(request, 'posts/about.html')


def support(request):
    return render(request, 'posts/support.html')