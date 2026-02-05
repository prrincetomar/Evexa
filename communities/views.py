from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Community, CommunityMember

from django.db.models import Count
from .models import Community, CommunityMember
from events.models import Tag

from .forms import CommunityForm

from django.http import HttpResponseForbidden


from django.db.models import Count

def community_list(request):
    query = request.GET.get('q')
    tag_id = request.GET.get('tag')
    sort = request.GET.get('sort', 'newest')
    role = request.GET.get('role', 'all')

    communities = Community.objects.all()

    # 🔍 search
    if query:
        communities = communities.filter(name__icontains=query)

    # 🏷️ tag filter
    if tag_id:
        communities = communities.filter(tags__id=tag_id)

    # 📊 sorting
    if sort == 'popular':
        communities = communities.annotate(
            member_count=Count('communitymember')
        ).order_by('-member_count')
    else:  # newest
        communities = communities.order_by('-created_at')

    joined_ids = set()
    created_ids = set()

    if request.user.is_authenticated:
        joined_ids = set(
            CommunityMember.objects.filter(user=request.user)
            .values_list('community_id', flat=True)
        )

        created_ids = set(
            Community.objects.filter(created_by=request.user)
            .values_list('id', flat=True)
        )

        # 🎯 ROLE FILTER
        if role == 'created':
            communities = communities.filter(created_by=request.user)

        elif role == 'joined':
            communities = communities.filter(id__in=joined_ids).exclude(
                created_by=request.user
            )

        elif role == 'not_joined':
            communities = communities.exclude(
                id__in=joined_ids
            ).exclude(
                created_by=request.user
            )

    # attach member_count + status
    for c in communities:
        c.member_count = CommunityMember.objects.filter(
            community=c
        ).count()

        if request.user.is_authenticated:
            if c.id in created_ids:
                c.status = "CREATOR"
            elif c.id in joined_ids:
                c.status = "MEMBER"
            else:
                c.status = None
        else:
            c.status = None

    tags = Tag.objects.all()

    return render(
        request,
        'communities/community_list.html',
        {
            'communities': communities,
            'tags': tags,
            'query': query,
            'selected_tag': tag_id,
            'selected_sort': sort,
            'selected_role': role,
        }
    )



@login_required
def join_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)

    already_joined = CommunityMember.objects.filter(
        user=request.user,
        community=community
    ).exists()

    if not already_joined:
        CommunityMember.objects.create(
            user=request.user,
            community=community
        )

    return redirect('/communities/')


@login_required
def leave_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)

    CommunityMember.objects.filter(
        user=request.user,
        community=community
    ).delete()

    return redirect('/communities/')

@login_required
def my_communities(request):
    filter_by = request.GET.get('filter', 'all')

    created_communities = Community.objects.filter(
        created_by=request.user
    )

    joined_communities = Community.objects.filter(
        communitymember__user=request.user
    )

    if filter_by == 'created':
        communities = created_communities

    elif filter_by == 'joined':
        communities = joined_communities.exclude(
            created_by=request.user
        )

    else:  # all
        communities = (created_communities | joined_communities).distinct()

    joined_ids = set(
        CommunityMember.objects.filter(user=request.user)
        .values_list('community_id', flat=True)
    )

    for community in communities:
        community.member_count = CommunityMember.objects.filter(
            community=community
        ).count()

        if community.created_by == request.user:
            community.status = "CREATOR"
        elif community.id in joined_ids:
            community.status = "MEMBER"
        else:
            community.status = ""

    return render(
        request,
        'communities/my_communities.html',
        {
            'communities': communities,
            'selected_filter': filter_by
        }
    )




def community_detail(request, community_id):
    community = get_object_or_404(Community, id=community_id)

    status = None

    if request.user.is_authenticated:
        if community.created_by == request.user:
            status = "CREATOR"
        elif CommunityMember.objects.filter(
            user=request.user,
            community=community
        ).exists():
            status = "MEMBER"

    member_count = CommunityMember.objects.filter(
        community=community
    ).count()

    return render(
        request,
        'communities/community_detail.html',
        {
            'community': community,
            'status': status,
            'member_count': member_count,
        }
    )

@login_required
def create_community(request):
    if request.method == 'POST':
        form = CommunityForm(request.POST)
        if form.is_valid():
            community = form.save(commit=False)
            community.created_by = request.user
            community.save()
            form.save_m2m()
            CommunityMember.objects.create(
                user=request.user,
                community=community
        )
        return redirect('/communities/')
    else:
        form = CommunityForm()

    return render(
        request,
        'communities/create_community.html',
        {'form': form}
    )

@login_required
def edit_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)

    # 🔐 only creator can edit
    if community.created_by != request.user:
        return HttpResponseForbidden("You are not allowed to edit this community")

    if request.method == 'POST':
        form = CommunityForm(request.POST, instance=community)
        if form.is_valid():
            form.save()
            return redirect('/communities/my/')
    else:
        form = CommunityForm(instance=community)

    return render(
        request,
        'communities/edit_community.html',
        {
            'form': form,
            'community': community
        }
    )