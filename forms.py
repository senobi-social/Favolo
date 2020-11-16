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
    email = forms.CharField(label='email', widget=forms.TextInput(attrs={'placeholder':'メールアドレス', 'class':'form-control'}))
    enter_password = forms.CharField(label='password', widget=forms.PasswordInput(attrs={'placeholder':'パスワード', 'class':'form-control'}))
    retype_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'パスワード（確認）', 'class':'form-control'}))

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
    email = forms.CharField(label='email', widget=forms.TextInput(attrs={'placeholder':'メールアドレス', 'class':'form-control'}))
    password = forms.CharField(label='password', widget=forms.PasswordInput(attrs={'placeholder':'パスワード', 'class':'form-control'}))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        return email
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        return password

class SettingsUsernameForm(forms.Form):
    new_username = forms.CharField(label='new_username', widget=forms.TextInput(attrs={'placeholder':'新規ユーザーネーム', 'class':'form-control'}))

    def clean_new_username(self):
        new_username = self.cleaned_data.get('new_username')
        return new_username

class SettingsPasswordForm(forms.Form):
    email = forms.CharField(label='email', widget=forms.TextInput(attrs={'placeholder':'メールアドレス', 'class':'form-control'}))
    new_password = forms.CharField(label='new_password', widget=forms.PasswordInput(attrs={'placeholder':'新規パスワード', 'class':'form-control'}))
    retype_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'新規パスワード（確認）', 'class':'form-control'}))  

    def clean_email(self):
        email = self.cleaned_data.get('email')
        return email

    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password')
        if len(new_password) < 5:
            raise forms.ValidationError('New Password must contain 5 or more characters.')
        return new_password

    def clean(self):
        super(SettingsPasswordForm, self).clean() #python2系の書き方らしいので注意
        new_password = self.cleaned_data.get('new_password')
        retyped = self.cleaned_data.get('retype_password')
        if new_password and retyped and (new_password != retyped):
            self.add_error('retype_password', 'This does not match with the above.') 

    def save(self):
        email = self.cleaned_data.get('email')
        new_password = self.cleaned_data.get('new_password')
        exist_user = User.objects.get(username = email)
        exist_user.set_password(new_password)
        exist_user.save()
        return new_password, email


class SettingsDesignForm(forms.Form):
    new_design = forms.IntegerField(label='new_design', widget=forms.NumberInput(attrs={'placeholder':'デザイン', 'class':'form-control'}))

    def clean_new_design(self):
        new_design = self.cleaned_data.get('new_design')
        return new_design

class SettingsIntroductionForm(forms.Form):
    new_title = forms.CharField(label='new_title', widget=forms.TextInput)
    new_comment = forms.CharField(label='new_comment', widget=forms.TextInput)

    def clean_new_title(self):
        new_title = self.cleaned_data.get('new_title')
        return new_title

    def clean_new_comment(self):
        new_comment = self.cleaned_data.get('new_comment')
        return new_comment


