from django.shortcuts import render, redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Event, Endpoint  # Import the Endpoint model
import logging
import json
from django.core.serializers import serialize
from datetime import datetime, timedelta
from django.db.models import Count, Q
from django.contrib.auth import login, authenticate
from .forms import UserRegisterForm
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import EndpointForm, CustomJSForm 
import uuid
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from .utils import sanitize_js
from django.contrib.admin.views.decorators import staff_member_required
from django import forms
from .forms import UserProfileForm
from django.core.paginator import Paginator

logger = logging.getLogger(__name__)

@login_required
def register_endpoint(request):
    if request.method == 'POST':
        form = EndpointForm(request.POST)
        if form.is_valid():
            endpoint = form.save(commit=False)
            endpoint.user = request.user
            endpoint.api_key = uuid.uuid4()
            endpoint.save()
            return redirect('event_statistics')  # Redirect to a relevant page
    else:
        form = EndpointForm()
    return render(request, 'register_endpoint.html', {'form': form})

def validate_api_key(request):
    api_key = request.headers.get('API-Key')
    if not api_key:
        return None, JsonResponse({"error": "API key required"}, status=400)

    try:
        endpoint = Endpoint.objects.get(api_key=api_key)
        return endpoint, None
    except Endpoint.DoesNotExist:
        return None, JsonResponse({"error": "Invalid API key"}, status=403)

class EventAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        event_data = request.data
        logger.debug(f"Event data received: {event_data}")
        event = Event.objects.create(
            endpoint=request.user.endpoint_set.first(),
            type=event_data.get('type'),
            path=event_data.get('path'),
            details=event_data
        )
        logger.info(f"Event created: {event}")
        return Response({"status": "success"}, status=201)

def parse_datetime(dt_str):
    try:
        return datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
        return datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%SZ')

def summarize_user_journey(events):
    summary = {}
    for event in events:
        session_id = event['details'].get('session_id', 'default_session_id')
        if session_id not in summary:
            summary[session_id] = []
        summary[session_id].append(event)
    return summary

def analyze_journey(summary):
    insights = {}
    for session_id, events in summary.items():
        journey = ""
        for event in events:
            journey += f"{event['timestamp']}: {event['type']} on {event['path']}\n"
            if event['type'] == 'pageview' and '/payment/' in event['path']:
                insights[session_id] = "User completed the order."
                break  # No need to check further if the order is completed
            elif event['type'] == 'pageview' and '/checkout/' in event['path']:
                if 'duration' not in [e['type'] for e in events]:
                    insights[session_id] = "User visited checkout page but did not complete purchase."
                else:
                    insights[session_id] = "User spent time on checkout page but did not complete purchase."
        
        if session_id not in insights:
            insights[session_id] = "User did not reach checkout page."
    
    return insights


@login_required
def event_statistics(request):
    user = request.user
    path = request.GET.get('path', None)
    selected_session_id = request.GET.get('session_id', None)
    
    if path:
        try:
            endpoint = Endpoint.objects.get(user=user, url=path)
            endpoints = [endpoint]  # Ensure endpoints is defined as a list
        except Endpoint.DoesNotExist:
            # Broader matching if exact match fails
            endpoints = Endpoint.objects.filter(user=user, url__startswith=path.split('/')[0] + '//' + path.split('/')[2])
            if not endpoints:
                return JsonResponse({"error": "You do not have access to this endpoint's data"}, status=403)
    else:
        endpoints = Endpoint.objects.filter(user=user)

    events = Event.objects.filter(endpoint__in=endpoints).order_by('timestamp')

    events_json = serialize('json', events)
    events_data = [event['fields'] for event in json.loads(events_json)]

    scroll_sessions = {}
    user_profiles = {}  # Dictionary to store user profiles
    last_event_time = None
    session_counter = 0
    last_event_type = None

    for event in events_data:
        event_time = parse_datetime(event['timestamp'])  # Added missing event_time parsing
        event['timestamp'] = event_time  # Store parsed datetime object

        session_id = event['details'].get('session_id', 'default_session_id')  # Extract session ID

        if session_id not in user_profiles:
            user_profiles[session_id] = []

        user_profiles[session_id].append({
            'type': event['type'],
            'path': event['path'],
            'timestamp': event_time.strftime('%Y-%m-%d %H:%M:%S'),
            'details': event['details']
        })

        if event['type'] == 'scroll':
            if last_event_time and (event_time - last_event_time > timedelta(minutes=1) or last_event_type != 'scroll'):
                session_counter += 1
            session_key = (event['path'], f"{session_id}_{session_counter}")
            if session_key not in scroll_sessions:
                scroll_sessions[session_key] = event
            else:
                max_depth = max(float(scroll_sessions[session_key]['details']['depth']), float(event['details']['depth']))
                scroll_sessions[session_key]['details']['depth'] = "{:.2f}".format(max_depth)
        last_event_time = event_time
        last_event_type = event['type']

    success_paths = [
        'http://127.0.0.1:8080/payment/stripe/',
        'http://127.0.0.1:8080/payment/paypal/'
    ]

    payment_pageviews = Event.objects.filter(endpoint__in=endpoints, path__in=success_paths).count()
    total_pageviews = Event.objects.filter(endpoint__in=endpoints, type='pageview').count()

    payment_percentage = (payment_pageviews / total_pageviews * 100) if total_pageviews > 0 else 0

    success_events = Event.objects.filter(endpoint__in=endpoints, path__in=success_paths).order_by('timestamp')
    success_json = serialize('json', success_events)
    success_data = [event['fields'] for event in json.loads(success_json)]

    success_list = [{
        'path': event['path'],
        'timestamp': parse_datetime(event['timestamp']).strftime('%Y-%m-%d %H:%M:%S')  # Format timestamp
    } for event in success_data]

    final_events = list(scroll_sessions.values()) + [event for event in events_data if event['type'] != 'scroll']

    if path:
        pageview_counts = Event.objects.filter(endpoint__in=endpoints, path__icontains=path, type='pageview').values('path').annotate(count=Count('id'))
    else:
        pageview_counts = Event.objects.filter(endpoint__in=endpoints, type='pageview').values('path').annotate(count=Count('id'))
    pageview_counts_data = {item['path']: item['count'] for item in pageview_counts}
    pageview_counts_json = json.dumps(pageview_counts_data)

    user_profiles = summarize_user_journey(events_data)
    insights = analyze_journey(user_profiles)

    # Pagination logic
    if selected_session_id and selected_session_id in user_profiles:
        selected_session = user_profiles[selected_session_id]
        paginator = Paginator(selected_session, 20)  # Show 20 events per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    else:
        page_obj = None

    context = {
        'successes': success_list,
        'events': final_events,
        'events_json': json.dumps(final_events, default=str),  # Ensure JSON serialization
        'pageview_counts_json': pageview_counts_json,
        'payment_percentage': payment_percentage,
        'user_profiles': user_profiles,  # Pass user profiles to the template
        'insights': insights,
        'selected_session_id': selected_session_id,
        'page_obj': page_obj
    }
    return render(request, 'statistics.html', context)






@login_required
def payment_success(request):
    user = request.user
    success_paths = [
        'http://127.0.0.1:3000/payment/stripe/',
        'http://127.0.0.1:3000/payment/paypal/'
    ]
    
    endpoints = Endpoint.objects.filter(user=user, url__in=success_paths)
    success_events = Event.objects.filter(endpoint__in=endpoints).order_by('timestamp')
    
    events_json = serialize('json', success_events)
    events_data = [event['fields'] for event in json.loads(events_json)]
    
    success_data = [{
        'path': event['path'],
        'timestamp': event['timestamp']
    } for event in events_data]

    return render(request, 'payment_success.html', {'successes': success_data})

def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a default endpoint for the new user
            Endpoint.objects.create(user=user, url='http://default.url', api_key=uuid.uuid4())
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

def tracking_script(request, endpoint_id):
    endpoint = get_object_or_404(Endpoint, id=endpoint_id)
    custom_js = endpoint.custom_js if endpoint.reviewed else ''

    script = f"""
    (function() {{
      const apiKey = '{endpoint.api_key}';
      const sessionId = getSessionId();

      function getSessionId() {{
        let sessionId = localStorage.getItem('sessionId');
        if (!sessionId) {{
          sessionId = 'sess_' + Math.random().toString(36).substr(2, 9);
          localStorage.setItem('sessionId', sessionId);
        }}
        return sessionId;
      }}
    
      const sendEvent = (eventData) => {{
        eventData.session_id = sessionId;  // Include session ID in the event data
        const endpoint = 'http://127.0.0.1:8000/api/events';
        fetch(endpoint, {{
          method: 'POST',
          headers: {{
            'Content-Type': 'application/json',
            'API-Key': apiKey
          }},
          body: JSON.stringify(eventData),
          keepalive: true
        }}).then(response => {{
          if (!response.ok) {{
            throw new Error('Network response was not ok');
          }}
          return response.json();
        }}).then(data => {{
          console.log('Success:', data);
        }}).catch(error => {{
          console.error('Error sending event:', error);
        }});
      }};
    
      // Page View and Visit Duration
      sendEvent({{ type: 'pageview', path: window.location.href }});
      window.addEventListener('unload', () => {{
        sendEvent({{
          type: 'duration',
          path: window.location.href,
          duration: Date.now() - performance.timing.navigationStart
        }});
      }});
    
      // Click Tracking
      document.addEventListener('click', (e) => {{
        sendEvent({{ type: 'click', path: window.location.href, target: e.target.tagName }});
      }});
    
      // Scroll Depth
      window.addEventListener('scroll', () => {{
        const scrolledPercentage = ((window.scrollY + window.innerHeight) / document.documentElement.scrollHeight) * 100;
        sendEvent({{ type: 'scroll', path: window.location.href, depth: scrolledPercentage.toFixed(2) }});
      }});
    
      // Form Interactions - Simplified Example
      document.addEventListener('submit', (e) => {{
        sendEvent({{ type: 'form_submit', path: window.location.href, formId: e.target.id }});
      }});
    
      document.addEventListener('mouseenter', (event) => {{
        if (event.target.classList.contains('hover-sensitive')) {{
          sendEvent({{
            type: 'hover',
            path: window.location.href,
            target: event.target.tagName
          }});
        }}
      }}, true);
      
      // Custom user-defined JavaScript
      {custom_js}
    
    }})();
    """
    return HttpResponse(script, content_type="application/javascript")

@login_required
def manage_endpoints(request):
    if request.method == 'POST':
        if 'add_endpoint' in request.POST:
            form = EndpointForm(request.POST)
            if form.is_valid():
                endpoint = form.save(commit=False)
                endpoint.user = request.user
                endpoint.save()
                return redirect('manage_endpoints')
        
        elif 'add_custom_js' in request.POST:
            js_form = CustomJSForm(request.POST, user=request.user)
            if js_form.is_valid():
                endpoint = js_form.cleaned_data['endpoint']
                endpoint.custom_js = sanitize_js(js_form.cleaned_data['custom_js'])
                endpoint.reviewed = False  # Mark as pending review
                endpoint.save()
                return redirect('manage_endpoints')

    else:
        form = EndpointForm()
        js_form = CustomJSForm(user=request.user)

    endpoints = Endpoint.objects.filter(user=request.user)
    return render(request, 'manage_endpoints.html', {'form': form, 'js_form': js_form, 'endpoints': endpoints})

def delete_endpoint(request, endpoint_id):
    endpoint = get_object_or_404(Endpoint, id=endpoint_id, user=request.user)
    endpoint.delete()
    return redirect('manage_endpoints')

@staff_member_required
def approve_custom_js(request):
    pending_endpoints = Endpoint.objects.filter(reviewed=False)
    if request.method == 'POST':
        endpoint_id = request.POST.get('endpoint_id')
        action = request.POST.get('action')
        endpoint = get_object_or_404(Endpoint, id=endpoint_id)
        if action == 'approve':
            endpoint.reviewed = True
        elif action == 'reject':
            endpoint.custom_js = ''
        endpoint.save()
        return redirect('approve_custom_js')
    return render(request, 'approve_custom_js.html', {'endpoints': pending_endpoints})

class CustomJSForm(forms.Form):
    endpoint = forms.ModelChoiceField(queryset=Endpoint.objects.none(), label="Select Endpoint")
    custom_js = forms.CharField(widget=forms.Textarea(attrs={'rows': 5, 'cols': 40}), label="Custom JS")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['endpoint'].queryset = Endpoint.objects.filter(user=user)

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'profile.html', {'form': form})