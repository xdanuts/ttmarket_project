from django import forms
from store.models import MyUser, Order
from django.contrib.auth.forms import UserCreationForm


class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = MyUser
        fields = ['email', 'first_name', 'last_name', 'password1', 'password2']


class LoginForm(forms.Form):
    email = forms.EmailField(required=True, label='E-mail')
    password = forms.CharField(required=True, max_length=255, label='Password', widget=forms.PasswordInput)


class ContactForm(forms.Form):
    subject = forms.CharField(max_length=50, required=True)
    name = forms.CharField(max_length=20, required=True)
    from_email = forms.EmailField(max_length=50, required=True)
    message = forms.CharField(
        max_length=500,
        required=True,
        widget=forms.Textarea(),
        help_text='Write here your message!'
    )


class DeliveryForm(forms.ModelForm):
    phone_number = forms.CharField()

    class Meta:
        model = Order
        fields = [
            'emailAddress',
            'shippingName',
            'shippingAddress1',
            'shippingCity',
            'shippingPostcode',
            'shippingCountry'
        ]

    def __init__(self, *args, **kwargs):
        super(DeliveryForm, self).__init__(*args, **kwargs)
        self.fields['emailAddress'].required = True
        self.fields['shippingName'].required = True
        self.fields['shippingAddress1'].required = True
        self.fields['shippingCity'].required = True
        self.fields['shippingPostcode'].required = True
        self.fields['shippingCountry'].required = True

    def save(self, commit=True):
        return super(DeliveryForm, self).save(commit=commit)
