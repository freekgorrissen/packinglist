from app.forms import (
    AccommodationTypeForm,
    ActivityForm,
    DestinationCategoryForm,
    FamilyMemberForm,
)
from app.models import AccommodationType, Activity, DestinationCategory, FamilyMember
from app.views.crud_factory import CrudConfig, make_create_view, make_delete_view, make_list_view, make_update_view

MEMBER_CONFIG = CrudConfig(
    model=FamilyMember,
    form_class=FamilyMemberForm,
    list_url_name='member_list',
    create_url_name='member_create',
    update_url_name='member_update',
    delete_url_name='member_delete',
    singular='Family Member',
    plural='Family Members',
)

DESTINATION_CONFIG = CrudConfig(
    model=DestinationCategory,
    form_class=DestinationCategoryForm,
    list_url_name='destination_list',
    create_url_name='destination_create',
    update_url_name='destination_update',
    delete_url_name='destination_delete',
    singular='Destination',
    plural='Destinations',
)

ACTIVITY_CONFIG = CrudConfig(
    model=Activity,
    form_class=ActivityForm,
    list_url_name='activity_list',
    create_url_name='activity_create',
    update_url_name='activity_update',
    delete_url_name='activity_delete',
    singular='Activity',
    plural='Activities',
)

ACCOMMODATION_CONFIG = CrudConfig(
    model=AccommodationType,
    form_class=AccommodationTypeForm,
    list_url_name='accommodation_list',
    create_url_name='accommodation_create',
    update_url_name='accommodation_update',
    delete_url_name='accommodation_delete',
    singular='Accommodation',
    plural='Accommodations',
)

MemberListView = make_list_view(MEMBER_CONFIG)
MemberCreateView = make_create_view(MEMBER_CONFIG)
MemberUpdateView = make_update_view(MEMBER_CONFIG)
MemberDeleteView = make_delete_view(MEMBER_CONFIG)

DestinationListView = make_list_view(DESTINATION_CONFIG)
DestinationCreateView = make_create_view(DESTINATION_CONFIG)
DestinationUpdateView = make_update_view(DESTINATION_CONFIG)
DestinationDeleteView = make_delete_view(DESTINATION_CONFIG)

ActivityListView = make_list_view(ACTIVITY_CONFIG)
ActivityCreateView = make_create_view(ACTIVITY_CONFIG)
ActivityUpdateView = make_update_view(ACTIVITY_CONFIG)
ActivityDeleteView = make_delete_view(ACTIVITY_CONFIG)

AccommodationListView = make_list_view(ACCOMMODATION_CONFIG)
AccommodationCreateView = make_create_view(ACCOMMODATION_CONFIG)
AccommodationUpdateView = make_update_view(ACCOMMODATION_CONFIG)
AccommodationDeleteView = make_delete_view(ACCOMMODATION_CONFIG)
