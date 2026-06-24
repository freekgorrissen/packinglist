from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

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


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123',
        )
        self.client.login(username='testuser', password='testpass123')
        self.section = PackingSection.objects.create(name='Clothing', sort_order=1)
        self.beach = DestinationCategory.objects.create(name='Beach')
        self.swimming = Activity.objects.create(name='Swimming')
        self.camping = AccommodationType.objects.create(name='Camping')
        self.alex = FamilyMember.objects.create(name='Alex')
        self.jordan = FamilyMember.objects.create(name='Jordan')

        PackingItem.objects.create(name='Passport', section=self.section, always=True)
        self.swimsuit = PackingItem.objects.create(name='Swimsuit', section=self.section)
        self.swimsuit.destinations.add(self.beach)
        self.swimsuit.accommodations.add(self.camping)

        self.trip = Trip.objects.create(name='Beach trip')
        self.trip.family_members.set([self.alex, self.jordan])
        self.trip.destinations.set([self.beach])
        self.trip.activities.set([self.swimming])
        self.trip.accommodations.set([self.camping])

    def test_home_page_loads(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Packing List')

    def test_member_crud_flow(self):
        response = self.client.post(
            reverse('member_create'),
            {'name': 'Casey', 'member_type': 'child', 'icon': 'child', 'notes': ''},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(FamilyMember.objects.filter(name='Casey').exists())

        member = FamilyMember.objects.get(name='Casey')
        response = self.client.get(reverse('member_list'))
        self.assertContains(response, 'Casey')

        response = self.client.post(
            reverse('member_update', args=[member.pk]),
            {'name': 'Casey Updated', 'member_type': 'child', 'icon': 'child', 'notes': 'Kid'},
        )
        self.assertEqual(response.status_code, 302)
        member.refresh_from_db()
        self.assertEqual(member.name, 'Casey Updated')

    def test_member_form_shows_distinct_icon_options(self):
        response = self.client.get(reverse('member_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'bi-person-standing-dress')
        self.assertContains(response, 'bi-person-arms-up')
        self.assertContains(response, 'member-icon-emoji')

    def test_packing_list_view_shows_member_icon(self):
        self.alex.icon = 'woman'
        self.alex.save()
        PackingItem.objects.create(
            name='Toothbrush',
            section=self.section,
            packing_allocation='individual',
            always=True,
        )
        response = self.client.get(reverse('trip_packing_list', args=[self.trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'bi-person-standing-dress')
        self.assertContains(response, 'Alex')

    def test_packing_list_view_shows_group_subheaders(self):
        sam = FamilyMember.objects.create(name='Sam', member_type=MemberType.CHILD)
        self.trip.family_members.add(sam)
        PackingItem.objects.create(
            name='First aid kit',
            section=self.section,
            packing_allocation=PackingAllocation.ADULTS_CHILDREN,
            always=True,
        )
        response = self.client.get(reverse('trip_packing_list', args=[self.trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Adults')
        self.assertContains(response, 'Children')
        self.assertContains(response, 'First aid kit')
        self.assertNotContains(response, 'First aid kit (Adults)')

    def test_packing_list_view_shows_shared_subheader(self):
        response = self.client.get(reverse('trip_packing_list', args=[self.trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Shared')
        self.assertContains(response, 'Passport')

    def test_packing_list_view_shows_person_subheaders(self):
        PackingItem.objects.create(
            name='Toothbrush',
            section=self.section,
            packing_allocation='individual',
            always=True,
        )
        response = self.client.get(reverse('trip_packing_list', args=[self.trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'column-header')
        self.assertContains(response, 'Alex')
        self.assertContains(response, 'Toothbrush')
        self.assertNotContains(response, 'Toothbrush (Alex)')

    def test_packing_list_view_shows_matching_items(self):
        response = self.client.get(reverse('trip_packing_list', args=[self.trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Swimsuit')
        self.assertContains(response, 'Passport')

    def test_trip_create_via_form(self):
        response = self.client.post(
            reverse('trip_create'),
            {
                'name': 'Mountain hike',
                'start_date': '',
                'end_date': '',
                'family_members': [self.alex.pk],
                'destinations': [self.beach.pk],
                'activities': [self.swimming.pk],
                'accommodations': [self.camping.pk],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Trip.objects.filter(name='Mountain hike').exists())

    def test_item_form_requires_category_when_not_always(self):
        response = self.client.post(
            reverse('item_create'),
            {
                'name': 'Missing categories',
                'section': self.section.pk,
                'notes': '',
                'packing_allocation': 'shared',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'For destinations, accommodations, and family members')
        self.assertFalse(PackingItem.objects.filter(name='Missing categories').exists())

    def test_item_form_always_clears_trip_categories_not_family_members(self):
        response = self.client.post(
            reverse('item_create'),
            {
                'name': 'Always item',
                'section': self.section.pk,
                'notes': '',
                'always': 'on',
                'packing_allocation': 'shared',
                'destinations': [self.beach.pk],
                'family_members': [self.alex.pk],
            },
        )
        self.assertEqual(response.status_code, 302)
        item = PackingItem.objects.get(name='Always item')
        self.assertTrue(item.always)
        self.assertEqual(item.destinations.count(), 0)
        self.assertEqual(list(item.family_members.all()), [self.alex])
        self.assertFalse(item.weather_hot)
        self.assertFalse(item.weather_cold)

    def test_item_form_always_clears_weather_when_submitted(self):
        response = self.client.post(
            reverse('item_create'),
            {
                'name': 'Hot always item',
                'section': self.section.pk,
                'notes': '',
                'always': 'on',
                'packing_allocation': 'shared',
                'weather_hot': 'on',
            },
        )
        self.assertEqual(response.status_code, 302)
        item = PackingItem.objects.get(name='Hot always item')
        self.assertFalse(item.weather_hot)
        self.assertFalse(item.weather_cold)

    def test_item_form_save_and_add_new(self):
        response = self.client.post(
            reverse('item_create'),
            {
                'name': 'Reusable item',
                'section': self.section.pk,
                'notes': '',
                'packing_allocation': 'shared',
                'destinations': [self.beach.pk],
                'save_and_add': '1',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('item_create'))
        self.assertTrue(PackingItem.objects.filter(name='Reusable item').exists())

    def test_item_form_batch_add_creates_multiple_items(self):
        response = self.client.post(
            reverse('item_create'),
            {
                'batch_add': 'on',
                'batch_names': ['Sun hat', 'Sandals', ''],
                'section': self.section.pk,
                'notes': 'Beach gear',
                'packing_allocation': 'shared',
                'destinations': [self.beach.pk],
            },
        )
        self.assertEqual(response.status_code, 302)
        items = PackingItem.objects.filter(name__in=['Sun hat', 'Sandals'])
        self.assertEqual(items.count(), 2)
        for item in items:
            self.assertEqual(item.notes, 'Beach gear')
            self.assertEqual(list(item.destinations.all()), [self.beach])

    def test_item_form_batch_add_requires_names(self):
        response = self.client.post(
            reverse('item_create'),
            {
                'batch_add': 'on',
                'batch_names': ['', ''],
                'section': self.section.pk,
                'notes': '',
                'packing_allocation': 'shared',
                'destinations': [self.beach.pk],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter at least one item name for batch add')
        self.assertEqual(PackingItem.objects.count(), 2)

    def test_item_form_layout_elements(self):
        response = self.client.get(reverse('item_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Batch add')
        self.assertContains(response, 'data-member-type="all"')
        self.assertContains(response, 'data-member-type="adult"')
        self.assertContains(response, 'data-member-type="child"')
        self.assertContains(response, 'data-member-type="pet"')
        self.assertContains(response, 'name="save_and_add"', count=2)
        self.assertNotContains(response, '<textarea')

    def test_item_list_shows_tags(self):
        response = self.client.get(reverse('item_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Swimsuit')
        self.assertContains(response, 'Beach')
        self.assertContains(response, 'Camping')

    def test_item_list_shows_weather_tags(self):
        self.swimsuit.weather_hot = True
        self.swimsuit.save()
        response = self.client.get(reverse('item_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hot')
        self.assertNotContains(response, '>Cold</span>')
