# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from scrum.models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'v.sauler@ejemplo.com',
            'class': 'flex h-10 w-full rounded-md border border-input px-3 py-2 text-sm ring-offset-background file:border-0 file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 bg-gray-800 placeholder:text-zinc-400 text-white'
        })
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo electrónico',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Victor Sauler Portal',
            'class': 'flex h-10 w-full rounded-md border border-input px-3 py-2 text-sm ring-offset-background file:border-0 file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 bg-gray-800 placeholder:text-zinc-400 text-white'
        })
        self.fields['password1'].label = 'Contraseña'
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Contraseña',
            'class': 'flex h-10 w-full rounded-md border border-input px-3 py-2 text-sm ring-offset-background file:border-0 file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 bg-gray-800 placeholder:text-zinc-400 text-white'
        })
        self.fields['password2'].label = 'Confirma la contraseña'
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Repite la contraseña',
            'class': 'flex h-10 w-full rounded-md border border-input px-3 py-2 text-sm ring-offset-background file:border-0 file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 bg-gray-800 placeholder:text-zinc-400 text-white'
        })