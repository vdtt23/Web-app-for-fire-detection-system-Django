from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings as django_settings
from posts.models import SensorData
from django.utils import timezone
from django.utils.dateparse import parse_date

def register_view(request):
    if request.user.is_authenticated:
        return redirect('/')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not username or not email or not password1:
            error = "All fields are required."
        elif password1 != password2:
            error = "Passwords do not match."
        elif User.objects.filter(username=username).exists():
            error = "Username already taken."
        elif User.objects.filter(email=email).exists():
            error = "An account with this email already exists."
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                is_active=False,  # inactive until email is verified
            )

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            verify_url = request.build_absolute_uri(f'/verify-email/{uid}/{token}/')

            send_mail(
                subject='Verify your Fili account',
                message=(
                    f'Hi {username},\n\n'
                    f'Click the link below to verify your email and activate your account:\n\n'
                    f'{verify_url}\n\n'
                    f'This link expires after 24 hours.\n\n'
                    f'\u2014 Fili Fire Detection System'
                ),
                from_email=django_settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )

            return redirect('/verify-pending/')

    return render(request, 'posts/register.html', {'error': error})


def verify_pending_view(request):
    return render(request, 'posts/verify_pending.html')


def verify_email_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, OverflowError):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'posts/verify_success.html')

    return render(request, 'posts/verify_failed.html')


def forgot_password_view(request):
    if request.user.is_authenticated:
        return redirect('/')

    sent = False
    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if not email:
            error = "Please enter your email address."
        else:
            try:
                user = User.objects.get(email=email, is_active=True)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_url = request.build_absolute_uri(f'/reset-password/{uid}/{token}/')
                send_mail(
                    subject='Reset your Fili password',
                    message=(
                        f'Hi {user.username},\n\n'
                        f'Click the link below to reset your password:\n\n'
                        f'{reset_url}\n\n'
                        f'This link expires after 24 hours.\n'
                        f'If you did not request this, ignore this email.\n\n'
                        f'\u2014 Fili Fire Detection System'
                    ),
                    from_email=django_settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except User.DoesNotExist:
                pass  # don't reveal whether the email exists
            sent = True  # always show "check your email" to avoid enumeration

    return render(request, 'posts/forgot_password.html', {'sent': sent, 'error': error})


def reset_password_view(request, uidb64, token):
    error = None
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, OverflowError):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        return render(request, 'posts/reset_password_invalid.html')

    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        if not password1:
            error = "Password cannot be empty."
        elif password1 != password2:
            error = "Passwords do not match."
        else:
            user.set_password(password1)
            user.save()
            return redirect('/login/?reset=1')

    return render(request, 'posts/reset_password.html', {'error': error, 'uidb64': uidb64, 'token': token})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'),
        )
        if user is not None:
            login(request, user)
            return redirect(request.GET.get('next', '/'))
        return render(request, 'posts/login.html', {'form': {'errors': True}})
    return render(request, 'posts/login.html', {'form': {}})

def logout_view(request):
    logout(request)
    return redirect('/login/')


@login_required(login_url='/login/')
def account_view(request):
    profile_error = None
    profile_success = None
    account_error = None
    account_success = None

    if request.method == 'POST':
        form_type = request.POST.get('form_type', '').strip()

        if form_type == 'profile':
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()

            if not email:
                profile_error = 'Email is required.'
            elif User.objects.exclude(pk=request.user.pk).filter(email=email).exists():
                profile_error = 'This email is already used by another account.'
            else:
                request.user.first_name = first_name
                request.user.last_name = last_name
                request.user.email = email
                request.user.save()
                profile_success = 'User information updated successfully.'

        elif form_type == 'account':
            username = request.POST.get('username', '').strip()
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            if not username:
                account_error = 'Username is required.'
            elif User.objects.exclude(pk=request.user.pk).filter(username=username).exists():
                account_error = 'Username already taken.'
            elif not request.user.check_password(current_password):
                account_error = 'Current password is incorrect.'
            elif new_password and new_password != confirm_password:
                account_error = 'New passwords do not match.'
            else:
                request.user.username = username
                if new_password:
                    request.user.set_password(new_password)
                request.user.save()
                if new_password:
                    update_session_auth_hash(request, request.user)
                account_success = 'Account information updated successfully.'

    return render(
        request,
        'posts/account.html',
        {
            'profile_error': profile_error,
            'profile_success': profile_success,
            'account_error': account_error,
            'account_success': account_success,
        },
    )


@login_required(login_url='/login/')
def home(request):
    return render(request, 'posts/home.html')

@login_required(login_url='/login/')
def dashboard(request):
    nodes = SensorData.objects.order_by('-created_at')[:10]

    fire_count = SensorData.objects.filter(status="FIRE").count()
    warning_count = SensorData.objects.filter(status="WARNING").count()

    return render(request, 'posts/dashboard.html', {
        'nodes': nodes,
        'fire_count': fire_count,
        'warning_count': warning_count
    })

@login_required(login_url='/login/')
def chart_data(request):
    qs = SensorData.objects.order_by('-created_at')[:20][::-1]  

    data = {
        "labels": [timezone.localtime(d.created_at).strftime("%H:%M:%S") for d in qs],
        "temp": [d.temperature for d in qs],
        "smoke": [d.smoke for d in qs],
        "humidity": [d.humidity for d in qs],
    }
    return JsonResponse(data)

@login_required(login_url='/login/')
def latest_nodes(request):
    nodes = {}
    qs = SensorData.objects.order_by('-created_at')

    for n in qs:
        if n.node_id not in nodes:
            nodes[n.node_id] = {
                "node_id": n.node_id,
                "temperature": n.temperature,
                "smoke": n.smoke,
                "humidity": n.humidity,
                "status": n.status,
                "x": n.x,
                "y": n.y,
            }

    return JsonResponse(list(nodes.values()), safe=False)

@login_required(login_url='/login/')
def node_history(request, node_id):
    qs = SensorData.objects.filter(node_id=node_id)

    start_date = parse_date(request.GET.get("start_date", ""))
    end_date = parse_date(request.GET.get("end_date", ""))

    if start_date:
        qs = qs.filter(created_at__date__gte=start_date)
    if end_date:
        qs = qs.filter(created_at__date__lte=end_date)

    qs = qs.order_by('-created_at')[:20]

    data = [
        {
            "node_id": n.node_id,
            "temperature": n.temperature,
            "smoke": n.smoke,
            "humidity": n.humidity,
            "status": n.status,
            "created_at": timezone.localtime(n.created_at).strftime("%Y-%m-%d %H:%M:%S"),
        }
        for n in qs
    ]

    return JsonResponse(data, safe=False)

@login_required(login_url='/login/')
def alerts(request):
    alerts = SensorData.objects.filter(
        status__in=["FIRE", "WARNING"]
    ).order_by('-created_at')

    return render(request, 'posts/alerts.html', {
        'alerts': alerts
    })

@login_required(login_url='/login/')
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

@login_required(login_url='/login/')
def about(request):
    return render(request, 'posts/about.html')

@login_required(login_url='/login/')
def support(request):
    return render(request, 'posts/support.html')

@login_required(login_url='/login/')
def node_map(request):
    return render(request, 'posts/nodemap.html')


@login_required(login_url='/login/')
def heartbeat(request):
    import time
    request.session['last_heartbeat'] = int(time.time())
    return JsonResponse({'ok': True})