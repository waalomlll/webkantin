from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'customer'

urlpatterns = [
    path('', views.kantin_list, name='kantin'),
    path('kantin/<slug:kode>/', views.kedai_list, name='kedai'),
    path('kedai/<int:kedai_id>/', views.menu_list, name='menu'),
    path('keranjang/', views.keranjang, name='keranjang'),
    path('bayar/', views.bayar, name='bayar'),
    path('bayar/batal/', views.bayar_batal, name='bayar_batal'),
    path('pesanan/', views.pesanan_list, name='pesanan'),
    path('pesanan/<int:pk>/', views.pesanan_detail, name='pesanan_detail'),
    path('pesanan/<int:pk>/status/', views.pesanan_status, name='pesanan_status'),
    path('pesanan/<int:pk>/batal/', views.pesanan_batal, name='pesanan_batal'),
    path('masuk/', auth_views.LoginView.as_view(template_name='customer/masuk.html'), name='masuk'),
    path('keluar/', auth_views.LogoutView.as_view(), name='keluar'),
]
