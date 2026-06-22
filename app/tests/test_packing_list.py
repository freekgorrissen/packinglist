from django.test import TestCase

from app.models import (
    AccommodationType,
    Activity,
    DestinationCategory,
    FamilyMember,
    MemberType,
    PackingAllocation,
    PackingItem,
    PackingSection,
    Trip,
)
from app.services.packing_list import (
    generate_packing_list,
    group_by_section,
    group_for_display,
    item_matches_trip,
)


class PackingListServiceTests(TestCase):
    def setUp(self):
        self.section = PackingSection.objects.create(name='Gear', sort_order=1)
        self.beach = DestinationCategory.objects.create(name='Beach')
        self.mountains = DestinationCategory.objects.create(name='Mountains')
        self.swimming = Activity.objects.create(name='Swimming')
        self.hiking = Activity.objects.create(name='Hiking')
        self.camping = AccommodationType.objects.create(name='Camping')
        self.hotel = AccommodationType.objects.create(name='Hotel')
        self.alex = FamilyMember.objects.create(name='Alex', member_type=MemberType.ADULT)
        self.jordan = FamilyMember.objects.create(name='Jordan', member_type=MemberType.ADULT)
        self.sam = FamilyMember.objects.create(name='Sam', member_type=MemberType.CHILD)

        self.universal_item = PackingItem.objects.create(
            name='Passport',
            section=self.section,
            always=True,
            packing_allocation=PackingAllocation.SHARED,
        )
        self.beach_item = PackingItem.objects.create(
            name='Swimsuit',
            section=self.section,
        )
        self.beach_item.destinations.add(self.beach)

        self.swim_or_beach_item = PackingItem.objects.create(
            name='Sunscreen',
            section=self.section,
        )
        self.swim_or_beach_item.destinations.add(self.beach)
        self.swim_or_beach_item.activities.add(self.swimming)

        self.individual_item = PackingItem.objects.create(
            name='Toothbrush',
            section=self.section,
            packing_allocation=PackingAllocation.INDIVIDUAL,
            always=True,
        )

        self.member_specific_item = PackingItem.objects.create(
            name='Ski boots',
            section=self.section,
            packing_allocation=PackingAllocation.INDIVIDUAL,
        )
        self.member_specific_item.destinations.add(self.mountains)
        self.member_specific_item.family_members.add(self.alex)

        self.trip = Trip.objects.create(name='Beach camping')
        self.trip.family_members.set([self.alex, self.jordan, self.sam])
        self.trip.destinations.set([self.beach])
        self.trip.activities.set([self.swimming])
        self.trip.accommodations.set([self.camping])

    def test_universal_item_always_included(self):
        self.assertTrue(item_matches_trip(self.universal_item, self.trip))
        entries = [e for e in generate_packing_list(self.trip) if e.item.name == 'Passport']
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].label, 'Passport')

    def test_tagged_item_matches_on_category_and_family(self):
        swim_trip = Trip.objects.create(name='Pool trip')
        swim_trip.destinations.set([self.mountains])
        swim_trip.activities.set([self.swimming])
        swim_trip.accommodations.set([self.hotel])
        swim_trip.family_members.set([self.alex])

        names = [e.item.name for e in generate_packing_list(swim_trip)]
        self.assertIn('Sunscreen', names)

    def test_tagged_item_excluded_when_category_mismatch(self):
        mountain_trip = Trip.objects.create(name='Mountain hotel')
        mountain_trip.destinations.set([self.mountains])
        mountain_trip.accommodations.set([self.hotel])
        mountain_trip.family_members.set([self.alex])

        names = [e.item.name for e in generate_packing_list(mountain_trip)]
        self.assertNotIn('Swimsuit', names)

    def test_tagged_item_excluded_when_family_mismatch(self):
        alex_jordan_trip = Trip.objects.create(name='Parents only')
        alex_jordan_trip.destinations.set([self.beach])
        alex_jordan_trip.accommodations.set([self.camping])
        alex_jordan_trip.family_members.set([self.alex, self.jordan])

        sam_only = PackingItem.objects.create(name='Child life jacket', section=self.section)
        sam_only.destinations.add(self.beach)
        sam_only.family_members.add(self.sam)

        names = [e.item.name for e in generate_packing_list(alex_jordan_trip)]
        self.assertNotIn('Child life jacket', names)

    def test_tagged_item_excluded_when_no_trip_members(self):
        no_member_trip = Trip.objects.create(name='No members')
        no_member_trip.destinations.set([self.beach])
        no_member_trip.accommodations.set([self.camping])

        names = [e.item.name for e in generate_packing_list(no_member_trip)]
        self.assertNotIn('Swimsuit', names)

    def test_family_only_item_excluded_without_category_tags(self):
        family_only = PackingItem.objects.create(name='EpiPen', section=self.section)
        family_only.family_members.add(self.alex)

        self.assertFalse(item_matches_trip(family_only, self.trip))

    def test_individual_allocation_expansion(self):
        entries = generate_packing_list(self.trip)
        toothbrush_entries = [e for e in entries if e.item.name == 'Toothbrush']
        self.assertEqual(len(toothbrush_entries), 3)
        people = {e.person.name for e in toothbrush_entries}
        self.assertEqual(people, {'Alex', 'Jordan', 'Sam'})

    def test_shared_allocation_single_line(self):
        entries = generate_packing_list(self.trip)
        sunscreen_entries = [e for e in entries if e.item.name == 'Sunscreen']
        self.assertEqual(len(sunscreen_entries), 1)
        self.assertEqual(sunscreen_entries[0].label, 'Sunscreen')

    def test_adults_children_allocation(self):
        first_aid = PackingItem.objects.create(
            name='First aid kit',
            section=self.section,
            packing_allocation=PackingAllocation.ADULTS_CHILDREN,
            always=True,
        )

        entries = generate_packing_list(self.trip)
        kit_entries = [e for e in entries if e.item.name == 'First aid kit']
        self.assertEqual(len(kit_entries), 2)
        self.assertEqual(
            {e.label for e in kit_entries},
            {'First aid kit (Adults)', 'First aid kit (Children)'},
        )

    def test_member_specific_item_only_for_tagged_members(self):
        mountain_trip = Trip.objects.create(name='Mountain trip')
        mountain_trip.destinations.set([self.mountains])
        mountain_trip.accommodations.set([self.hotel])
        mountain_trip.family_members.set([self.alex, self.jordan])

        entries = generate_packing_list(mountain_trip)
        ski_entries = [e for e in entries if e.item.name == 'Ski boots']
        self.assertEqual(len(ski_entries), 1)
        self.assertEqual(ski_entries[0].person.name, 'Alex')

    def test_deduplication(self):
        duplicate = PackingItem.objects.create(
            name='Duplicate tag item',
            section=self.section,
        )
        duplicate.destinations.add(self.beach)
        duplicate.activities.add(self.swimming)

        entries = generate_packing_list(self.trip)
        duplicate_entries = [e for e in entries if e.item.name == 'Duplicate tag item']
        self.assertEqual(len(duplicate_entries), 1)

    def test_always_item_included_on_any_trip(self):
        always_item = PackingItem.objects.create(
            name='Wallet',
            section=self.section,
            always=True,
        )
        empty_trip = Trip.objects.create(name='Empty')
        names = [e.item.name for e in generate_packing_list(empty_trip)]
        self.assertIn('Wallet', names)

    def test_individual_with_tagged_family_members(self):
        glasses = PackingItem.objects.create(
            name='Glasses',
            section=self.section,
            always=True,
            packing_allocation=PackingAllocation.INDIVIDUAL,
        )
        glasses.family_members.add(self.alex, self.jordan)

        entries = generate_packing_list(self.trip)
        glasses_entries = [e for e in entries if e.item.name == 'Glasses']
        self.assertEqual(len(glasses_entries), 2)
        self.assertEqual(
            {e.label for e in glasses_entries},
            {'Glasses (Alex)', 'Glasses (Jordan)'},
        )

    def test_shared_with_tagged_family_members(self):
        glasses = PackingItem.objects.create(
            name='Glasses',
            section=self.section,
            always=True,
            packing_allocation=PackingAllocation.SHARED,
        )
        glasses.family_members.add(self.alex, self.jordan)

        entries = generate_packing_list(self.trip)
        glasses_entries = [e for e in entries if e.item.name == 'Glasses']
        self.assertEqual(len(glasses_entries), 1)
        self.assertEqual(glasses_entries[0].label, 'Glasses')

    def test_always_item_with_family_filter_excluded_when_no_trip_overlap(self):
        glasses = PackingItem.objects.create(
            name='Glasses',
            section=self.section,
            always=True,
            packing_allocation=PackingAllocation.INDIVIDUAL,
        )
        glasses.family_members.add(self.alex)

        empty_trip = Trip.objects.create(name='No members')
        names = [e.item.name for e in generate_packing_list(empty_trip)]
        self.assertNotIn('Glasses', names)

    def test_always_item_limited_to_tagged_family_members(self):
        child_item = PackingItem.objects.create(
            name='Diapers',
            section=self.section,
            always=True,
            packing_allocation=PackingAllocation.INDIVIDUAL,
        )
        child_item.family_members.add(self.sam)

        entries = generate_packing_list(self.trip)
        diaper_entries = [e for e in entries if e.item.name == 'Diapers']
        self.assertEqual(len(diaper_entries), 1)
        self.assertEqual(diaper_entries[0].person.name, 'Sam')

    def test_untagged_non_always_item_excluded(self):
        untagged = PackingItem.objects.create(
            name='Orphan item',
            section=self.section,
        )
        self.assertFalse(item_matches_trip(untagged, self.trip))
        names = [e.item.name for e in generate_packing_list(self.trip)]
        self.assertNotIn('Orphan item', names)

    def test_group_by_section(self):
        toiletries = PackingSection.objects.create(name='Toiletries', sort_order=2)
        PackingItem.objects.create(name='Soap', section=toiletries, always=True)

        entries = generate_packing_list(self.trip)
        grouped = group_by_section(entries)
        section_names = [section.name for section, _ in grouped]
        self.assertEqual(section_names[0], 'Gear')
        self.assertIn('Toiletries', section_names)

    def test_group_for_display_columns(self):
        entries = generate_packing_list(self.trip)
        display = group_for_display(entries)
        toiletries = next(
            section for section in display if section.section.name == 'Gear'
        )
        alex_column = next(
            column for column in toiletries.columns if column.label == 'Alex'
        )
        self.assertIn('Toothbrush', [entry.item.name for entry in alex_column.entries])

    def test_group_for_display_group_columns(self):
        PackingItem.objects.create(
            name='First aid kit',
            section=self.section,
            packing_allocation=PackingAllocation.ADULTS_CHILDREN,
            always=True,
        )
        entries = generate_packing_list(self.trip)
        display = group_for_display(entries)
        gear = next(section for section in display if section.section.name == 'Gear')
        column_labels = [column.label for column in gear.columns]
        self.assertEqual(column_labels.count('Adults'), 1)
        self.assertEqual(column_labels.count('Children'), 1)

    def test_group_for_display_shared_column(self):
        entries = generate_packing_list(self.trip)
        display = group_for_display(entries)
        gear = next(section for section in display if section.section.name == 'Gear')
        shared_column = next(
            (column for column in gear.columns if column.label == 'Shared'),
            None,
        )
        self.assertIsNotNone(shared_column)
        self.assertTrue(
            any(entry.item.name == 'Passport' for entry in shared_column.entries)
        )

    def test_empty_trip_still_includes_universal_items(self):
        empty_trip = Trip.objects.create(name='Empty')
        names = [e.item.name for e in generate_packing_list(empty_trip)]
        self.assertIn('Passport', names)
        self.assertNotIn('Swimsuit', names)

    def test_weather_item_included_when_trip_matches(self):
        self.trip.weather_hot = True
        self.trip.save()
        hot_item = PackingItem.objects.create(
            name='Sandals',
            section=self.section,
            weather_hot=True,
            always=True,
        )
        names = [e.item.name for e in generate_packing_list(self.trip)]
        self.assertIn('Sandals', names)

    def test_weather_item_excluded_when_trip_does_not_match(self):
        self.trip.weather_cold = True
        self.trip.save()
        hot_item = PackingItem.objects.create(
            name='Sandals',
            section=self.section,
            weather_hot=True,
            always=True,
        )
        names = [e.item.name for e in generate_packing_list(self.trip)]
        self.assertNotIn('Sandals', names)

    def test_weather_item_excluded_when_trip_has_no_weather(self):
        hot_item = PackingItem.objects.create(
            name='Sandals',
            section=self.section,
            weather_hot=True,
            always=True,
        )
        names = [e.item.name for e in generate_packing_list(self.trip)]
        self.assertNotIn('Sandals', names)

    def test_item_without_weather_unaffected_by_trip_weather(self):
        self.trip.weather_cold = True
        self.trip.save()
        names = [e.item.name for e in generate_packing_list(self.trip)]
        self.assertIn('Passport', names)
        self.assertIn('Swimsuit', names)

    def test_weather_item_included_without_accommodation_match(self):
        self.trip.weather_hot = True
        self.trip.accommodations.set([self.hotel])
        self.trip.save()
        sun_hat = PackingItem.objects.create(
            name='Sun hat',
            section=self.section,
            weather_hot=True,
        )
        sun_hat.accommodations.add(self.camping)

        names = [e.item.name for e in generate_packing_list(self.trip)]
        self.assertIn('Sun hat', names)
