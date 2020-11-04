from django import forms
from django.contrib.auth.models import User
from django.http import HttpResponse

class FavoloForm(forms.Form):
    # この順番がフォームの順番になる
    username = forms.CharField(label='username', widget=forms.TextInput(attrs={'class':'form-control'}))
    account = forms.CharField(label='account', widget=forms.TextInput(attrs={'class':'form-control'}))


class SignUpForm(forms.Form):
    username = forms.CharField(label='username', widget=forms.TextInput(attrs={'placeholder':'ユーザ名', 'class':'form-control'}))
    account = forms.CharField(label='account', widget=forms.TextInput(attrs={'placeholder':'Twitterアカウント名', 'class':'form-control'}))
    email = forms.CharField(label='email', widget=forms.TextInput)
    enter_password = forms.CharField(label='password', widget=forms.PasswordInput)
    retype_password = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        return username
    
    def clean_account(self):
        account = self.cleaned_data.get('account')
        return account

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError('The email has been already taken.')
        return email

    def clean_enter_password(self):
        password = self.cleaned_data.get('enter_password')
        if len(password) < 5:
            raise forms.ValidationError('Password must contain 5 or more characters.')
        return password

    def clean(self):
        super(SignUpForm, self).clean() #python2系の書き方らしいので注意
        password = self.cleaned_data.get('enter_password')
        retyped = self.cleaned_data.get('retype_password')
        if password and retyped and (password != retyped):
            self.add_error('retype_password', 'This does not match with the above.')

    def save(self):
        username = self.cleaned_data.get('username')
        account = self.cleaned_data.get('account')
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('enter_password')
        new_user = User.objects.create_user(username = email)
        new_user.set_password(password)
        new_user.save()
        return username, account, password

class LoginForm(forms.Form):
    email = forms.CharField(label='email', widget=forms.TextInput)
    password = forms.CharField(label='password', widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        return email
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        return password

