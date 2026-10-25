from rest_framework import serializers
from django.contrib.auth import get_user_model
User=get_user_model()
class QuerySerializer(serializers.Serializer):
    connection_id=serializers.IntegerField(min_value=1)
    question=serializers.CharField(max_length=500)

class RegistrationSerializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True,min_length=8,style={'input_style':'password'})
    class Meta:
        model=User
        fields= ["username", "email", "password"]
    def validate_username(self,value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "this usernamer is alraedy taken by other user"
            )
        return value
    def validate_email(self,value):
        if not value.strip():
            raise serializers.ValidationError(
                "email is requred"
            )
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "this email is alredy registerd"
            )
        return value

    def create(self,validate_data):
        return User.objects.create_user(**validate_data)


class DatabaseConnectionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=500)
    host = serializers.CharField(max_length=255)
    port = serializers.IntegerField(
        min_value=1,
        max_value=65535,
        default=5432
    )
    database = serializers.CharField(max_length=255)
    username = serializers.CharField(max_length=255)
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        allow_blank=False,
        max_length=1024
    )
