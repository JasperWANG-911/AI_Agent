from django.urls import path
from . import views

urlpatterns = [
    path('student_analysis/', views.student_analysis_view, name='student_analysis'),
    path('save_image/', views.save_image, name='save_image'),
]