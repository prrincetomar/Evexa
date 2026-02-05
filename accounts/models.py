from django.db import models
from django.contrib.auth.models import User
from events.models import Tag

from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=100, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    bio = models.TextField(blank=True)

    profile_pic = models.ImageField(
        upload_to="profile_pics/",
        blank=True,
        null=True
    )

    favourite_tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="interested_users"
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    SAFE signal:
    - Creates profile ONLY when user is created
    - Never assumes profile already exists
    """
    if created:
        Profile.objects.create(user=instance)
