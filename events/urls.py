from django.urls import path
from .views import (
    events_list,
    create_event,
    join_event,
    leave_event,
    my_events,
    event_detail,
    edit_event,
    edit_announcement,
    delete_announcement,
    cancel_event,
    delete_event,   # ✅ Phase 4.3
)

urlpatterns = [
    path('', events_list, name='events_list'),
    path('create/', create_event, name='create_event'),
    path('join/<int:event_id>/', join_event, name='join_event'),
    path('leave/<int:event_id>/', leave_event, name='leave_event'),
    path('my/', my_events, name='my_events'),
    path('edit/<int:event_id>/', edit_event, name='edit_event'),
    path('<int:event_id>/', event_detail, name='event_detail'),

    # Phase 3.2 — Announcements
    path(
        'announcements/edit/<int:announcement_id>/',
        edit_announcement,
        name='edit_announcement'
    ),
    path(
        'announcements/delete/<int:announcement_id>/',
        delete_announcement,
        name='delete_announcement'
    ),

    # Phase 3.3 — Event Cancellation
    path(
        'cancel/<int:event_id>/',
        cancel_event,
        name='cancel_event'
    ),

    # Phase 4.3 — Safe Event Deletion
    path(
        'delete/<int:event_id>/',
        delete_event,
        name='delete_event'
    ),
]
