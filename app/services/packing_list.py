"""Packing list generation service.

Matching rule:
- Items with always=True are included (when family members are tagged on the item,
  at least one must be on the trip).
- Other items are included when at least one destination, activity, or accommodation
  matches the trip AND at least one relevant family member is on the trip.
- When an item has weather type(s) selected, at least one must match a weather type on the trip.
  Matching weather is enough for inclusion (accommodation and other categories are not required).
"""

from dataclasses import dataclass

from app.models import (
    FamilyMember,
    MemberType,
    PackingAllocation,
    PackingItem,
    PackingSection,
    Trip,
)


@dataclass(frozen=True)
class PackingListEntry:
    section: PackingSection
    item: PackingItem
    person: FamilyMember | None = None
    group_label: str | None = None

    @property
    def label(self):
        if self.person:
            return f'{self.item.name} ({self.person.name})'
        if self.group_label:
            return f'{self.item.name} ({self.group_label})'
        return self.item.name


TagKey = tuple[str, int]


def _trip_category_keys(trip: Trip) -> set[TagKey]:
    keys: set[TagKey] = set()
    keys.update(('destination', pk) for pk in trip.destinations.values_list('pk', flat=True))
    keys.update(('activity', pk) for pk in trip.activities.values_list('pk', flat=True))
    keys.update(('accommodation', pk) for pk in trip.accommodations.values_list('pk', flat=True))
    return keys


def _item_category_keys(item: PackingItem) -> set[TagKey]:
    keys: set[TagKey] = set()
    keys.update(('destination', pk) for pk in item.destinations.values_list('pk', flat=True))
    keys.update(('activity', pk) for pk in item.activities.values_list('pk', flat=True))
    keys.update(('accommodation', pk) for pk in item.accommodations.values_list('pk', flat=True))
    return keys


def _category_matches_trip(item: PackingItem, trip: Trip) -> bool:
    item_categories = _item_category_keys(item)
    if not item_categories:
        return False
    trip_categories = _trip_category_keys(trip)
    return bool(item_categories & trip_categories)


def _family_matches_trip(item: PackingItem, trip: Trip) -> bool:
    trip_member_pks = set(trip.family_members.values_list('pk', flat=True))
    if not trip_member_pks:
        return False
    tagged_member_pks = set(item.family_members.values_list('pk', flat=True))
    if tagged_member_pks:
        return bool(tagged_member_pks & trip_member_pks)
    return True


def _weather_matches_trip(item: PackingItem, trip: Trip) -> bool:
    item_weather = {
        weather_type
        for weather_type, enabled in (
            ('hot', item.weather_hot),
            ('cold', item.weather_cold),
        )
        if enabled
    }
    if not item_weather:
        return True
    trip_weather = {
        weather_type
        for weather_type, enabled in (
            ('hot', trip.weather_hot),
            ('cold', trip.weather_cold),
        )
        if enabled
    }
    return bool(item_weather & trip_weather)


def _item_has_weather(item: PackingItem) -> bool:
    return item.weather_hot or item.weather_cold


def item_matches_trip(item: PackingItem, trip: Trip) -> bool:
    if not _weather_matches_trip(item, trip):
        return False
    if item.always:
        tagged_member_pks = set(item.family_members.values_list('pk', flat=True))
        if tagged_member_pks:
            trip_member_pks = set(trip.family_members.values_list('pk', flat=True))
            return bool(tagged_member_pks & trip_member_pks)
        return True
    if _item_has_weather(item):
        return _family_matches_trip(item, trip)
    return _category_matches_trip(item, trip) and _family_matches_trip(item, trip)


def _applicable_members(item: PackingItem, trip: Trip) -> list[FamilyMember]:
    trip_members = list(trip.family_members.all())
    tagged_members = list(item.family_members.all())
    if tagged_members:
        return [member for member in tagged_members if member in trip_members]
    return trip_members


def _line_targets_for_item(
    item: PackingItem,
    trip: Trip,
) -> list[tuple[FamilyMember | None, str | None]]:
    """Return (person, group_label) pairs for each packing list line."""
    members = _applicable_members(item, trip)
    allocation = item.packing_allocation

    if allocation == PackingAllocation.INDIVIDUAL:
        return [(member, None) for member in members]

    if allocation == PackingAllocation.SHARED:
        if members or not item.family_members.exists():
            return [(None, None)]
        return []

    if allocation == PackingAllocation.ADULTS_CHILDREN:
        targets: list[tuple[FamilyMember | None, str | None]] = []
        if any(member.member_type == MemberType.ADULT for member in members):
            targets.append((None, 'Adults'))
        if any(member.member_type == MemberType.CHILD for member in members):
            targets.append((None, 'Children'))
        if any(member.member_type == MemberType.PET for member in members):
            targets.append((None, 'Pets'))
        return targets

    return [(None, None)]


def generate_packing_list(trip: Trip) -> list[PackingListEntry]:
    entries: list[PackingListEntry] = []
    seen: set[tuple[int, int | None, str | None]] = set()

    items = (
        PackingItem.objects.select_related('section')
        .prefetch_related(
            'destinations',
            'activities',
            'accommodations',
            'family_members',
        )
    )

    for item in items:
        if not item_matches_trip(item, trip):
            continue

        for person, group_label in _line_targets_for_item(item, trip):
            key = (item.pk, person.pk if person else None, group_label)
            if key in seen:
                continue
            seen.add(key)
            entries.append(
                PackingListEntry(
                    section=item.section,
                    item=item,
                    person=person,
                    group_label=group_label,
                )
            )

    entries.sort(
        key=lambda e: (
            e.section.sort_order,
            e.section.name,
            e.item.name,
            e.group_label or '',
            e.person.name if e.person else '',
        )
    )
    return entries


def group_by_section(entries: list[PackingListEntry]) -> list[tuple[PackingSection, list[PackingListEntry]]]:
    grouped: list[tuple[PackingSection, list[PackingListEntry]]] = []
    current_section = None
    current_entries: list[PackingListEntry] = []

    for entry in entries:
        if entry.section != current_section:
            if current_section is not None:
                grouped.append((current_section, current_entries))
            current_section = entry.section
            current_entries = [entry]
        else:
            current_entries.append(entry)

    if current_section is not None:
        grouped.append((current_section, current_entries))

    return grouped


@dataclass(frozen=True)
class PackingColumnDisplay:
    label: str
    entries: list[PackingListEntry]
    member_icon: str | None = None


@dataclass(frozen=True)
class PackingSectionDisplay:
    section: PackingSection
    columns: list[PackingColumnDisplay]


GROUP_LABEL_ORDER = ('Adults', 'Children', 'Pets')


def group_for_display(entries: list[PackingListEntry]) -> list[PackingSectionDisplay]:
    """Group entries by section into columns for person, shared, and group allocations."""
    display: list[PackingSectionDisplay] = []

    for section, section_entries in group_by_section(entries):
        by_person: dict[int, list[PackingListEntry]] = {}
        shared_entries: list[PackingListEntry] = []
        by_group: dict[str, list[PackingListEntry]] = {}

        for entry in section_entries:
            if entry.person:
                by_person.setdefault(entry.person.pk, []).append(entry)
            elif entry.group_label:
                by_group.setdefault(entry.group_label, []).append(entry)
            else:
                shared_entries.append(entry)

        columns: list[PackingColumnDisplay] = []

        for person_entries in sorted(by_person.values(), key=lambda e: e[0].person.name):
            person = person_entries[0].person
            columns.append(
                PackingColumnDisplay(
                    label=person.name,
                    entries=person_entries,
                    member_icon=person.icon,
                )
            )

        if shared_entries:
            columns.append(PackingColumnDisplay(label='Shared', entries=shared_entries))

        for group_label, group_entries in sorted(
            by_group.items(),
            key=lambda group: (
                GROUP_LABEL_ORDER.index(group[0])
                if group[0] in GROUP_LABEL_ORDER
                else len(GROUP_LABEL_ORDER)
            ),
        ):
            columns.append(PackingColumnDisplay(label=group_label, entries=group_entries))

        display.append(PackingSectionDisplay(section=section, columns=columns))

    return display
