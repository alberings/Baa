from django.urls import path, include
from .views import EventAPIView
from . import views
from django.contrib.auth import views as auth_views
from django.urls import path
from .views import register_endpoint, tracking_script
from .views import manage_endpoints
from .views import delete_endpoint

urlpatterns = [
    path('api/events', EventAPIView.as_view(), name='event-api'),
    path('statistics/', views.event_statistics, name='event_statistics'),
    path('successes/', views.payment_success, name='payment_success'),
    path('accounts/', include('django.contrib.auth.urls')),  # Include built-in auth URLs
    path('register/', views.register, name='register'),  # Custom registration view
    path('', views.home, name='home'),  # Assuming you have a home view
    path('logout/', auth_views.LogoutView.as_view(template_name='logged_out.html'), name='logout'),  # Logout view
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),  # Login view
    path('register-endpoint/', views.register_endpoint, name='register_endpoint'),  # Register endpoint view
    path('tracking-script/<int:endpoint_id>/', tracking_script, name='tracking_script'),
    path('manage-endpoints/', manage_endpoints, name='manage_endpoints'),
    path('delete-endpoint/<int:endpoint_id>/', delete_endpoint, name='delete_endpoint'),
    path('profile/', views.profile, name='profile'),



]
