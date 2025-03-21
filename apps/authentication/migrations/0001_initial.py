# Generated by Django 4.2.20 on 2025-03-18 02:45

import apps.authentication.utils
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UserForgetPasswordRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Timestamp when the object was created.', verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('code', models.CharField(default=apps.authentication.utils.create_tracking_code_with_uuid, editable=False, max_length=16, verbose_name='Code')),
                ('email', models.EmailField(max_length=254, null=True, verbose_name='email')),
                ('phone_number', models.CharField(max_length=17, null=True, validators=[django.core.validators.RegexValidator(message='Phone number must be entered in the format: "+999999999". Up to 15 digits is allowed.', regex='^\\+?1?\\d{10,15}$')], verbose_name='Phone Number')),
                ('used', models.BooleanField(default=False, verbose_name='Used')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active?')),
            ],
            options={
                'verbose_name': 'User Forget Password Request',
                'verbose_name_plural': 'Users Forget Password Requests',
            },
        ),
        migrations.CreateModel(
            name='UserVerificationRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Timestamp when the object was created.', verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('code', models.CharField(default=apps.authentication.utils.create_tracking_code_with_uuid, editable=False, max_length=16, verbose_name='Code')),
                ('email', models.EmailField(max_length=254, null=True, verbose_name='email')),
                ('phone_number', models.CharField(max_length=17, null=True, validators=[django.core.validators.RegexValidator(message='Phone number must be entered in the format: "+999999999". Up to 15 digits is allowed.', regex='^\\+?1?\\d{10,15}$')], verbose_name='Phone Number')),
                ('used', models.BooleanField(default=False, verbose_name='Used')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active?')),
            ],
            options={
                'verbose_name': 'User Verification Request',
                'verbose_name_plural': 'Users Verification Requests',
            },
        ),
    ]
