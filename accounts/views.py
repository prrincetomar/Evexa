from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

from events.models import Event, EventRegistration
from communities.models import CommunityMember

from .forms import ProfileForm


@login_required
def profile(request):
    user = request.user
    # Handle case where profile doesn't exist
    profile, created = user.profile if hasattr(user, 'profile') else None, False
    
    if profile is None:
        from .models import Profile
        profile, created = Profile.objects.get_or_create(user=user)

    # Handle profile update
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)

    # Activity counts
    created_events_count = Event.objects.filter(created_by=user).count()
    joined_events_count = EventRegistration.objects.filter(user=user).count()
    joined_communities_count = CommunityMember.objects.filter(user=user).count()

    # Profile completion calculation
    filled = 0
    total = 6

    if profile.full_name:
        filled += 1
    if profile.age:
        filled += 1
    if profile.phone:
        filled += 1
    if profile.bio:
        filled += 1
    if profile.profile_pic:
        filled += 1
    if profile.favourite_tags.exists():
        filled += 1

    profile_completion = int((filled / total) * 100)

    return render(
        request,
        "accounts/profile.html",
        {
            "user": user,
            "form": form,
            "created_events_count": created_events_count,
            "joined_events_count": joined_events_count,
            "joined_communities_count": joined_communities_count,
            "profile_completion": profile_completion,
        }
    )


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/accounts/login/")
    else:
        form = UserCreationForm()

    return render(request, "accounts/register.html", {"form": form})


def home(request):
    return render(request, "home.html")
