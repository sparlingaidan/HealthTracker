from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search, name='search'),
    path('edit/', views.edit, name='edit'),
    path('update_percent/<int:log_id>/', views.update_percent, name='update_percent'),
    path('update_date/<int:log_id>/', views.update_date, name='update_date'),
    path('save_logItem/<int:fdcId>/', views.save_logItem, name='save_logItem'),
    path('delete_logItem/', views.delete_logItem, name='delete_logItem'),
]
