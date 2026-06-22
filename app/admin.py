from django.contrib import admin

from app.models import (
    AccommodationType,
    Activity,
    DestinationCategory,
    FamilyMember,
    PackingItem,
    PackingSection,
    Trip,
)


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name', 'member_type', 'icon']
    list_filter = ['member_type', 'icon']


@admin.register(DestinationCategory)
class DestinationCategoryAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(AccommodationType)
class AccommodationTypeAdmin(admin.ModelAdmin):
    search_fields = ['name']


class PackingItemInline(admin.TabularInline):
    model = PackingItem
    extra = 0


@admin.register(PackingSection)
class PackingSectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'sort_order']
    ordering = ['sort_order', 'name']
    inlines = [PackingItemInline]


@admin.register(PackingItem)
class PackingItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'section', 'always', 'packing_allocation', 'weather_hot', 'weather_cold']
    list_filter = ['section', 'always', 'packing_allocation', 'weather_hot', 'weather_cold']
    search_fields = ['name']
    filter_horizontal = [
        'destinations',
        'activities',
        'accommodations',
        'family_members',
    ]


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'weather_hot', 'weather_cold', 'created_at']
    list_filter = ['weather_hot', 'weather_cold']
    filter_horizontal = [
        'family_members',
        'destinations',
        'activities',
        'accommodations',
    ]
