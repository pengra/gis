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
from states.views import avail_maps_json
from django.conf.urls.static import static
from wxml.settings import DEBUG

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', avail_maps_json),
]


if DEBUG:
    urlpatterns += static('/visuals/', document_root='visuals/') + static('/raws/', document_root='raws/') + static('/redist/', document_root='redist/')
