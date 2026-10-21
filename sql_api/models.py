from django.db import models
from django.contrib.auth.models import User

class DatabaseConnection(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE, related_name="database_connections")
    name=models.CharField(max_length=500)
    db_type=models.CharField(max_length=30, default='postgresql')
    host=models.CharField(max_length=255)
    port=models.PositiveIntegerField(default=5432)
    database=models.CharField(max_length=255)
    username=models.CharField(max_length=255)
    encrypt_password=models.TextField()
    create_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} - {self.user.username}'