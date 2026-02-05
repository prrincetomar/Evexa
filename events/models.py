from django.db import models
from django.contrib.auth.models import User


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Event(models.Model):
    EVENT_STATES = [
        ('UPCOMING', 'Upcoming'),
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    title = models.CharField(max_length=100)
    interest = models.CharField(max_length=50)

    tags = models.ManyToManyField(Tag, blank=True)

    age_criteria = models.CharField(
        max_length=50,
        default="No age limit"
    )

    description = models.TextField(blank=True)

    mode = models.CharField(
        max_length=10,
        choices=[('Online', 'Online'), ('Offline', 'Offline')],
        default='Online'
    )

    venue_or_link = models.CharField(
        max_length=200,
        default="To be announced"
    )

    location = models.CharField(max_length=100)

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)

    max_participants = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Leave empty for unlimited participants"
    )

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    # ✅ Phase 3.3 — Cancellation support
    event_state = models.CharField(
        max_length=20,
        default="",
        blank=True
    )

    cancellation_reason = models.TextField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.title


class EventRegistration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} joined {self.event.title}"


class EventAnnouncement(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="announcements"
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Announcement for {self.event.title}"


class EventVisibilitySettings(models.Model):
    hide_completed_after_days = models.PositiveIntegerField(
        default=7,
        help_text="Hide completed events from public list after N days"
    )

    hide_cancelled_after_days = models.PositiveIntegerField(
        default=7,
        help_text="Hide cancelled events from public list after N days"
    )

    def __str__(self):
        return "Event Visibility Settings"

    class Meta:
        verbose_name = "Event Visibility Settings"
        verbose_name_plural = "Event Visibility Settings"
