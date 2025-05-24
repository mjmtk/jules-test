# core/migrations/0002_populate_reference_data.py
from django.db import migrations

def populate_data(apps, schema_editor):
    ClientStatus = apps.get_model('core', 'ClientStatus')
    ClientStatus.objects.bulk_create([
        ClientStatus(code='active', name='Active', description='Currently receiving services', display_order=1, is_active=True),
        ClientStatus(code='inactive', name='Inactive', description='Not currently active', display_order=2, is_active=True),
        ClientStatus(code='pending', name='Pending', description='Pending intake or assessment', display_order=3, is_active=True),
        ClientStatus(code='waitlisted', name='Waitlisted', description='On waitlist for services', display_order=4, is_active=True),
        ClientStatus(code='closed', name='Closed', description='Case closed, services completed or discontinued', display_order=5, is_active=True),
        ClientStatus(code='deceased', name='Deceased', description='Client is deceased', display_order=6, is_active=False),
        ClientStatus(code='deleted', name='Deleted', description='Client record soft deleted', display_order=99, is_active=False),
    ])

    Language = apps.get_model('core', 'Language')
    Language.objects.bulk_create([
        Language(code='en-NZ', name='English (New Zealand)', native_name='English', display_order=1, is_active=True),
        Language(code='mi-NZ', name='Te Reo Māori', native_name='Te Reo Māori', display_order=2, is_active=True),
        Language(code='sm-NZ', name='Samoan (New Zealand)', native_name='Gagana Samoa', display_order=3, is_active=True),
        Language(code='zh-CN', name='Mandarin', native_name='普通话', display_order=4, is_active=True),
        Language(code='hi-IN', name='Hindi', native_name='हिन्दी', display_order=5, is_active=True),
        Language(code='fr-FR', name='French', native_name='Français', display_order=6, is_active=True),
        Language(code='de-DE', name='German', native_name='Deutsch', display_order=7, is_active=True),
        Language(code='ko-KR', name='Korean', native_name='한국어', display_order=8, is_active=True),
        Language(code='ja-JP', name='Japanese', native_name='日本語', display_order=9, is_active=True),
        Language(code='other', name='Other', native_name='Other', display_order=99, is_active=True), # For less common languages
    ])

    Pronoun = apps.get_model('core', 'Pronoun')
    Pronoun.objects.bulk_create([
        Pronoun(code='he-him', display_text='He/Him', display_order=1, is_active=True),
        Pronoun(code='she-her', display_text='She/Her', display_order=2, is_active=True),
        Pronoun(code='they-them', display_text='They/Them', display_order=3, is_active=True),
        Pronoun(code='ze-hir', display_text='Ze/Hir', display_order=4, is_active=True),
        Pronoun(code='use-name', display_text='Use My Name', display_order=5, is_active=True),
        Pronoun(code='prefer-not-say', display_text='Prefer Not to Say', display_order=6, is_active=True),
        Pronoun(code='other', display_text='Other', display_order=99, is_active=True),
    ])

    SexValue = apps.get_model('core', 'SexValue')
    SexValue.objects.bulk_create([
        SexValue(code='male', name='Male', display_order=1, is_active=True),
        SexValue(code='female', name='Female', display_order=2, is_active=True),
        SexValue(code='intersex', name='Intersex', display_order=3, is_active=True),
        SexValue(code='unknown', name='Unknown', display_order=4, is_active=True),
        SexValue(code='prefer-not-say', name='Prefer Not to Say', display_order=5, is_active=True),
    ])

def unpopulate_data(apps, schema_editor):
    # This function can be used to reverse the data population if needed.
    # For this task, we'll keep it simple and just delete all data from these tables.
    # In a real-world scenario, you might want to be more specific about what you delete.
    ClientStatus = apps.get_model('core', 'ClientStatus')
    ClientStatus.objects.all().delete()

    Language = apps.get_model('core', 'Language')
    Language.objects.all().delete()

    Pronoun = apps.get_model('core', 'Pronoun')
    Pronoun.objects.all().delete()

    SexValue = apps.get_model('core', 'SexValue')
    SexValue.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'), # Ensure this depends on the previous migration
    ]

    operations = [
        migrations.RunPython(populate_data, reverse_code=unpopulate_data),
    ]
