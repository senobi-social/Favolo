from django.urls import path
from django.contrib.auth import views as auth_views
from .views import FavoloView
from . import views

app_name = 'favolo'

# 第１引数にはアドレスを指定
# 第２引数には使用するビュー関数を指定
# 第３引数にはこのパス自体の名前を指定

#path('login/', auth_views.LoginView.as_view(template_name="favolo/login.html"), name='login'),
#path('logout/', auth_views.LogoutView.as_view(next_page="favolo:test"), name='logout'),

urlpatterns = [
    path(r'', FavoloView.as_view(), name='index'),
    path('result', views.result, name='result'),
    path('profile', views.profile, name='profile'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.account_login, name='login'),
    path('logout/', views.account_logout, name='logout'),
    path('settings/username', views.settings_username, name='username'),
    path('settings/password', views.settings_password, name='password'),
    path('settings/design', views.settings_design, name='design'),
    path('settings/introduction', views.settings_introduction, name='introduction'),
    path('settings', views.settings, name='settings'),
]