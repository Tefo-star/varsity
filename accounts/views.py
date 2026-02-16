from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django import forms
from django.contrib.auth.models import User
from posts.models import UserActivity

UNIVERSITY_CHOICES = [
    ('ub', 'University of Botswana (UB)'),
    ('buan', 'Botswana University of Agriculture (BUAN)'),
    ('botho', 'Botho University'),
    ('limkokwing', 'Limkokwing University'),
    ('baisago', 'BA ISAGO University'),
    ('newera', 'New Era College'),
    ('gaborone', 'Gaborone University College'),
    ('boitekanelo', 'Boitekanelo College'),
    ('visitor', 'Visitor/Not a Student'),
]

class CustomUserCreationForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    university = forms.ChoiceField(choices=UNIVERSITY_CHOICES)
    
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'university']
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            # Save university to activity
            activity = UserActivity.objects.create(
                user=user,
                university=self.cleaned_data['university']
            )
        return user

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to Varsity Connect Botswana! 🎓')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')