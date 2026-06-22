from django.db import models


class MemberType(models.TextChoices):
    ADULT = 'adult', 'Adult'
    CHILD = 'child', 'Child'
    PET = 'pet', 'Pet'


class MemberIcon(models.TextChoices):
    MAN = 'man', 'Man'
    WOMAN = 'woman', 'Woman'
    CHILD = 'child', 'Child'
    DOG = 'dog', 'Dog'


class FamilyMember(models.Model):
    name = models.CharField(max_length=100)
    member_type = models.CharField(
        max_length=10,
        choices=MemberType.choices,
        default=MemberType.ADULT,
    )
    icon = models.CharField(
        max_length=10,
        choices=MemberIcon.choices,
        default=MemberIcon.MAN,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class DestinationCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'destination categories'

    def __str__(self):
        return self.name


class Activity(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'activities'

    def __str__(self):
        return self.name


class AccommodationType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class PackingSection(models.Model):
    name = models.CharField(max_length=100)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class PackingAllocation(models.TextChoices):
    INDIVIDUAL = 'individual', 'Individual'
    ADULTS_CHILDREN = 'adults_children', 'Adults / children'
    SHARED = 'shared', 'Shared'


class PackingItem(models.Model):
    name = models.CharField(max_length=200)
    section = models.ForeignKey(
        PackingSection,
        on_delete=models.CASCADE,
        related_name='items',
    )
    notes = models.TextField(blank=True)
    always = models.BooleanField(
        default=False,
        help_text='Include this item on every trip, regardless of categories.',
    )
    packing_allocation = models.CharField(
        max_length=20,
        choices=PackingAllocation.choices,
        default=PackingAllocation.SHARED,
    )
    destinations = models.ManyToManyField(
        DestinationCategory,
        blank=True,
        related_name='packing_items',
    )
    activities = models.ManyToManyField(
        Activity,
        blank=True,
        related_name='packing_items',
    )
    accommodations = models.ManyToManyField(
        AccommodationType,
        blank=True,
        related_name='packing_items',
    )
    family_members = models.ManyToManyField(
        FamilyMember,
        blank=True,
        related_name='packing_items',
    )
    weather_hot = models.BooleanField(default=False)
    weather_cold = models.BooleanField(default=False)

    class Meta:
        ordering = ['section__sort_order', 'section__name', 'name']

    def __str__(self):
        return self.name

    def has_tags(self):
        return (
            self.destinations.exists()
            or self.activities.exists()
            or self.accommodations.exists()
            or self.family_members.exists()
        )


class Trip(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    family_members = models.ManyToManyField(FamilyMember, related_name='trips')
    destinations = models.ManyToManyField(DestinationCategory, related_name='trips')
    activities = models.ManyToManyField(Activity, blank=True, related_name='trips')
    accommodations = models.ManyToManyField(AccommodationType, related_name='trips')
    weather_hot = models.BooleanField(default=False)
    weather_cold = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name
