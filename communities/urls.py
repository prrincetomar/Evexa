from django.urls import path
from .views import (
    community_list,
    create_community,
    edit_community,
    join_community,
    leave_community,
    my_communities,
    community_detail,
)


urlpatterns = [
    path('', community_list, name='community_list'),

    # 🔹 CREATE & EDIT (must come BEFORE <int:community_id>)
    path('create/', create_community, name='create_community'),
    path('edit/<int:community_id>/', edit_community, name='edit_community'),

    # 🔹 USER ACTIONS
    path('join/<int:community_id>/', join_community, name='join_community'),
    path('leave/<int:community_id>/', leave_community, name='leave_community'),
    path('my/', my_communities, name='my_communities'),

    # 🔹 DETAIL (ALWAYS LAST)
    path('<int:community_id>/', community_detail, name='community_detail'),
]
