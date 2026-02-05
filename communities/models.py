from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from events.models import Tag

class Community(models.Model):
    name = models.CharField(max_length=100)
    interest = models.CharField(max_length=50)  # legacy
    description = models.TextField()

    rules = models.TextField(
        default="Be respectful to all members."
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        default=1
    )

    created_at = models.DateTimeField(
        default=timezone.now
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True
    )

    def __str__(self):
        return self.name


class CommunityMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} joined {self.community.name}"