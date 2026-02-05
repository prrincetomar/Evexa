from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.utils import timezone
from datetime import datetime

from .models import (
    Event,
    EventRegistration,
    Tag,
    EventAnnouncement
)
from .forms import EventForm

from django.contrib import messages

from .models import EventVisibilitySettings


def compute_event_lifecycle(event):
    """
    FINAL lifecycle rules (authoritative & fixed):

    Priority:
    1. CANCELLED always wins (manual action)
    2. COMPLETED if event time has passed
    3. UPCOMING / ONGOING by time
    """

    now = timezone.now()

    start_dt = timezone.make_aware(
        datetime.combine(event.date, event.start_time)
    )

    end_dt = None
    if event.end_time:
        end_dt = timezone.make_aware(
            datetime.combine(event.date, event.end_time)
        )

    # ✅ RULE 1: Cancelled ALWAYS wins
    if event.event_state == "CANCELLED":
        return "cancelled"

    # ✅ RULE 2: Completed by time
    if end_dt and now > end_dt:
        return "completed"

    # ✅ RULE 3: Time-based
    if now < start_dt:
        return "upcoming"

    return "ongoing"







from django.utils import timezone
from datetime import timedelta
from .models import Event, EventRegistration, Tag
from .models import EventVisibilitySettings  # ✅ REQUIRED


from datetime import timedelta
from django.utils import timezone

def events_list(request):
    query = request.GET.get("q")
    tag_id = request.GET.get("tag")
    sort = request.GET.get("sort", "upcoming")
    role = request.GET.get("role", "all")
    lifecycle_filter = request.GET.get("lifecycle", "all")

    qs = Event.objects.all()

    # 🔍 SEARCH
    if query:
        qs = qs.filter(title__icontains=query)

    # 🏷 TAG FILTER
    if tag_id:
        qs = qs.filter(tags__id=tag_id)

    # ⚙️ VISIBILITY SETTINGS
    settings = EventVisibilitySettings.objects.first()
    hide_completed_days = settings.hide_completed_after_days if settings else 0
    hide_cancelled_days = settings.hide_cancelled_after_days if settings else 0

    now = timezone.now()
    events = []

    for event in qs:
        lifecycle = compute_event_lifecycle(event)
        event.lifecycle = lifecycle

        # 🟢 UPCOMING & ONGOING → ALWAYS VISIBLE
        if lifecycle in ["upcoming", "ongoing"]:
            events.append(event)
            continue

        # 🔵 COMPLETED VISIBILITY
        if lifecycle == "completed":
            if hide_completed_days == 0:
                continue

            if event.end_time:
                end_dt = timezone.make_aware(
                    datetime.combine(event.date, event.end_time)
                )
                if now - end_dt <= timedelta(days=hide_completed_days):
                    events.append(event)
            continue

        # 🔴 CANCELLED VISIBILITY
        if lifecycle == "cancelled":
            if hide_cancelled_days == 0:
                continue

            # Use event date as reference (stable)
            cancel_dt = timezone.make_aware(
                datetime.combine(event.date, event.start_time)
            )

            if now - cancel_dt <= timedelta(days=hide_cancelled_days):
                events.append(event)
            continue

    # 🔁 LIFECYCLE FILTER (UI)
    if lifecycle_filter != "all":
        events = [e for e in events if e.lifecycle == lifecycle_filter]

    # 🔃 SORTING
    if sort == "popular":
        events.sort(
            key=lambda e: EventRegistration.objects.filter(event=e).count(),
            reverse=True
        )
    elif sort == "newest":
        events.sort(key=lambda e: e.id, reverse=True)
    else:
        events.sort(key=lambda e: e.date)

    # 👤 USER RELATIONSHIP
    joined_ids = set()
    created_ids = set()

    if request.user.is_authenticated:
        joined_ids = set(
            EventRegistration.objects.filter(user=request.user)
            .values_list("event_id", flat=True)
        )
        created_ids = set(
            Event.objects.filter(created_by=request.user)
            .values_list("id", flat=True)
        )

    # 👥 ROLE FILTER
    if role == "created":
        events = [e for e in events if e.id in created_ids]
    elif role == "joined":
        events = [e for e in events if e.id in joined_ids and e.id not in created_ids]
    elif role == "not_joined":
        events = [e for e in events if e.id not in joined_ids and e.id not in created_ids]

    # 🎯 DECORATE
    for event in events:
        event.join_count = EventRegistration.objects.filter(event=event).count()
        if event.id in created_ids:
            event.status = "CREATOR"
        elif event.id in joined_ids:
            event.status = "MEMBER"
        else:
            event.status = None

    return render(
        request,
        "events/events_list.html",
        {
            "events": events,
            "query": query,
            "tags": Tag.objects.all(),
            "selected_tag": tag_id,
            "selected_sort": sort,
            "selected_role": role,
            "selected_lifecycle": lifecycle_filter,
        }
    )





@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            form.save_m2m()

            EventRegistration.objects.create(
                user=request.user,
                event=event
            )

            return redirect('/events/')
    else:
        form = EventForm()

    return render(request, 'events/create_event.html', {'form': form})


@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if event.created_by != request.user:
        return HttpResponseForbidden("You are not allowed to edit this event")

    lifecycle = compute_event_lifecycle(event)

    if lifecycle in ["cancelled", "completed"]:
        messages.warning(
            request,
            "This event can no longer be edited."
        )
        return redirect(f"/events/{event.id}/")

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect('/events/my/')
    else:
        form = EventForm(instance=event)

    return render(request, 'events/edit_event.html', {'form': form, 'event': event})


@login_required
def join_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    lifecycle = compute_event_lifecycle(event)

    # ❌ Block join for cancelled or completed events
    if lifecycle in ["cancelled", "completed"]:
        messages.warning(
            request,
            "You cannot join this event anymore."
        )
        return redirect(f"/events/{event.id}/")

    # Capacity check
    if event.max_participants:
        count = EventRegistration.objects.filter(event=event).count()
        if count >= event.max_participants:
            messages.warning(
                request,
                "This event is already full."
            )
            return redirect(f"/events/{event.id}/")

    EventRegistration.objects.get_or_create(
        user=request.user,
        event=event
    )
    return redirect(f"/events/{event.id}/")



@login_required
def leave_event(request, event_id):
    EventRegistration.objects.filter(
        user=request.user,
        event_id=event_id
    ).delete()
    return redirect('/events/')


def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # 🔥 FIX: compute lifecycle ONCE
    event.lifecycle = compute_event_lifecycle(event)

    status = None
    if request.user.is_authenticated:
        if event.created_by == request.user:
            status = "CREATOR"
        elif EventRegistration.objects.filter(user=request.user, event=event).exists():
            status = "MEMBER"

    announcements = EventAnnouncement.objects.filter(
        event=event
    ).order_by('-created_at')

    # ✅ Posting announcements ONLY if allowed
    if (
        request.method == "POST"
        and status == "CREATOR"
        and event.lifecycle in ["upcoming", "ongoing"]
    ):
        message = request.POST.get("message")
        if message:
            EventAnnouncement.objects.create(
                event=event,
                message=message,
                created_by=request.user
            )
            return redirect(f"/events/{event.id}/")

    return render(
        request,
        'events/event_detail.html',
        {
            'event': event,
            'status': status,
            'join_count': EventRegistration.objects.filter(event=event).count(),
            'announcements': announcements,
        }
    )


@login_required
def my_events(request):
    filter_by = request.GET.get('filter', 'all')

    created_events = Event.objects.filter(created_by=request.user)
    joined_events = Event.objects.filter(
        eventregistration__user=request.user
    )

    if filter_by == 'created':
        events = created_events
    elif filter_by == 'joined':
        events = joined_events.exclude(created_by=request.user)
    else:
        events = (created_events | joined_events).distinct()

    joined_ids = set(
        EventRegistration.objects.filter(user=request.user)
        .values_list('event_id', flat=True)
    )

    for event in events:
        event.join_count = EventRegistration.objects.filter(event=event).count()

        if event.created_by == request.user:
            event.status = "CREATOR"
        elif event.id in joined_ids:
            event.status = "MEMBER"
        else:
            event.status = None

        event.lifecycle = compute_event_lifecycle(event)

    return render(
        request,
        'events/my_events.html',
        {
            'events': events,
            'selected_filter': filter_by
        }
    )


@login_required
def edit_announcement(request, announcement_id):
    announcement = get_object_or_404(EventAnnouncement, id=announcement_id)
    event = announcement.event

    # 🔐 Permission check
    if event.created_by != request.user:
        return HttpResponseForbidden("You are not allowed to edit this announcement")

    # 🔒 Completed events → silently redirect (no ugly page)
    if compute_event_lifecycle(event) == "completed":
        messages.warning(
        request,
        "This event is completed. Announcements can no longer be edited."
    )
        return redirect(f"/events/{event.id}/")

    if request.method == "POST":
        message = request.POST.get("message")
        if message:
            announcement.message = message
            announcement.save()
            return redirect(f"/events/{event.id}/")

    return render(
        request,
        "events/edit_announcement.html",
        {
            "announcement": announcement,
            "event": event,
        }
    )


@login_required
def delete_announcement(request, announcement_id):
    announcement = get_object_or_404(EventAnnouncement, id=announcement_id)
    event = announcement.event

    # 🔐 Permission check
    if event.created_by != request.user:
        return HttpResponseForbidden("You are not allowed to delete this announcement")

    # ✅ Deletion allowed EVEN IF event is completed
    if request.method == "POST":
        announcement.delete()
        return redirect(f"/events/{event.id}/")

    return render(
        request,
        "events/delete_announcement.html",
        {
            "announcement": announcement,
            "event": event,
        }
    )

@login_required
def cancel_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # 🔐 Creator-only
    if event.created_by != request.user:
        return HttpResponseForbidden("You are not allowed to cancel this event")

    lifecycle = compute_event_lifecycle(event)

    # ❌ Only UPCOMING or ONGOING can be cancelled
    if lifecycle not in ["upcoming", "ongoing"]:
        messages.warning(
            request,
            "This event cannot be cancelled anymore."
        )
        return redirect(f"/events/{event.id}/")

    if request.method == "POST":
        reason = request.POST.get("cancellation_reason", "").strip()

        event.event_state = "CANCELLED"
        event.cancellation_reason = reason if reason else None
        event.save()

        messages.success(
            request,
            "Event has been cancelled successfully."
        )

        return redirect(f"/events/{event.id}/")

    return render(
        request,
        "events/cancel_event.html",
        {
            "event": event
        }
    )
@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # 🔐 Creator-only
    if event.created_by != request.user:
        return HttpResponseForbidden("You are not allowed to delete this event")

    lifecycle = compute_event_lifecycle(event)

    # ❌ Deletion allowed ONLY for completed or cancelled
    if lifecycle not in ["completed", "cancelled"]:
        messages.warning(
            request,
            "Only completed or cancelled events can be deleted."
        )
        return redirect(f"/events/{event.id}/")

    if request.method == "POST":
        event.delete()
        messages.success(
            request,
            "Event deleted permanently."
        )
        return redirect("/events/my/")

    return render(
        request,
        "events/delete_event.html",
        {
            "event": event,
            "lifecycle": lifecycle
        }
    )
