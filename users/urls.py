from django.urls import path
from .import views

app_name = 'users'
urlpatterns = [
    path('register/', views.register, name='register'),
    path('account_management/', views.account, name='account'),
    path('user/<int:user_id>', views.user_center, name='user_center'),
    # path('password_reset', views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset_X', views.password_reset_X, name='password_reset_X')

]