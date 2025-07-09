from rest_framework import serializers
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'fullname']
        read_only_fields = ['id']

    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username