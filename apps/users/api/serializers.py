from rest_framework import serializers

from apps.users.models import User
from apps.authentication.tasks import send_account_verification_email


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'uuid', 'email', 'is_active', 'logo',
            'phone_number', 'first_name', 'last_name',
            'gender', 'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at', 'is_active')

    def update(self, instance, validated_data):
        email = validated_data.pop('email', None)
        if email and email != instance.email:
            send_account_verification_email.delay(str(instance.pk), email)
        return super().update(instance, validated_data)
