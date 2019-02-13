"""wxml URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from django.conf.urls.static import static
from wxml.settings import DEBUG, MEDIA_URL, MEDIA_ROOT
from states.views import DataView, StateListView, APIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home/main.html')),
    path('data/<uuid:id>/', DataView.as_view()),
    path('data/', DataView.as_view()),
    path('api/', APIView.as_view()),
    path('states/', StateListView.as_view()),
    path('documentation/', TemplateView.as_view(template_name='documentation/overview.html')),
    path('documentation/algorithm/', TemplateView.as_view(template_name='documentation/algorithm.html')),
    # case study link
    # documentation
    # features
]

if DEBUG:
    urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
