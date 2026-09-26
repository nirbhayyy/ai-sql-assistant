from rest_framework import serializers

class Queriserializer(serializers.Serializer):
    Question=serializers.CharField(max_lenght=500)
    