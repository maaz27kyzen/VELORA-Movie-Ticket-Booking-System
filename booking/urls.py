from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('movie/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    path('show/<int:show_id>/seats/', views.seat_selection, name='seat_selection'),
    path('book/checkout/', views.booking_checkout, name='booking_checkout'),
    path('book/confirm/', views.confirm_booking, name='confirm_booking'),
    path('booking/<int:booking_id>/confirmation/', views.booking_success, name='booking_success'),
]
