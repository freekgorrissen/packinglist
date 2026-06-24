from django.core.management.base import BaseCommand

from app.models import (
    AccommodationType,
    Activity,
    DestinationCategory,
    FamilyMember,
    MemberIcon,
    MemberType,
    PackingAllocation,
    PackingItem,
    PackingSection,
)


class Command(BaseCommand):
    help = 'Seed default categories, family members, and sample packing items'

    def handle(self, *args, **options):
        members = {}
        for name, member_type, icon in [
            ('Freek', MemberType.ADULT, MemberIcon.MAN),
            ('Dominique', MemberType.ADULT, MemberIcon.WOMAN),
            ('Maya', MemberType.CHILD, MemberIcon.CHILD),
            ('Nata', MemberType.CHILD, MemberIcon.DOG),
        ]:
            member, _ = FamilyMember.objects.get_or_create(
                name=name,
                defaults={'member_type': member_type, 'icon': icon},
            )
            if member.member_type != member_type or member.icon != icon:
                member.member_type = member_type
                member.icon = icon
                member.save()
            members[name] = member

        destinations = {}
        for name in ['Beach', 'Mountains', 'City', 'Forest']:
            destinations[name], _ = DestinationCategory.objects.get_or_create(name=name)

        activities = {}
        for name in ['Swimming', 'Hiking', 'Skiing']:
            activities[name], _ = Activity.objects.get_or_create(name=name)

        accommodations = {}
        for name in ['Camping', 'Hotel', 'Airbnb', 'Guest']:
            accommodations[name], _ = AccommodationType.objects.get_or_create(name=name)

        sections = {}
        for sort_order, name in enumerate(['Clothing', 'Toiletries', 'Gear', 'Documents'], start=1):
            sections[name], _ = PackingSection.objects.get_or_create(
                name=name,
                defaults={'sort_order': sort_order},
            )

        samples = [
            ('Toothbrush', 'Toiletries', PackingAllocation.INDIVIDUAL, True, [], [], [], []),
            ('Passport', 'Documents', PackingAllocation.SHARED, True, [], [], [], []),
            ('Swimsuit', 'Clothing', PackingAllocation.INDIVIDUAL, False, ['Beach'], ['Swimming'], [], []),
            ('Hiking boots', 'Gear', PackingAllocation.INDIVIDUAL, False, ['Mountains', 'Forest'], ['Hiking'], [], []),
            ('Ski jacket', 'Clothing', PackingAllocation.INDIVIDUAL, False, ['Mountains'], ['Skiing'], [], []),
            ('Tent', 'Gear', PackingAllocation.SHARED, False, [], [], ['Camping'], []),
            ('Sleeping bag', 'Gear', PackingAllocation.ADULTS_CHILDREN, False, [], [], ['Camping'], []),
            ('Sunscreen', 'Toiletries', PackingAllocation.SHARED, False, ['Beach'], ['Swimming'], [], []),
        ]

        for name, section_name, allocation, always, dests, acts, accs, _members in samples:
            item, created = PackingItem.objects.get_or_create(
                name=name,
                section=sections[section_name],
                defaults={'packing_allocation': allocation, 'always': always},
            )
            if created or options.get('force'):
                item.packing_allocation = allocation
                item.always = always
                item.save()
                if always:
                    item.destinations.clear()
                    item.activities.clear()
                    item.accommodations.clear()
                    item.family_members.clear()
                else:
                    item.destinations.set([destinations[d] for d in dests])
                    item.activities.set([activities[a] for a in acts])
                    item.accommodations.set([accommodations[a] for a in accs])

        self.stdout.write(self.style.SUCCESS('Default data seeded successfully.'))
