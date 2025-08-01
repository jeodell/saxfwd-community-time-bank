# Generated by Django 5.0.2 on 2025-07-27 22:23

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_rename_is_onboarded_application_is_orientation_completed_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='timebankledger',
            name='donated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='donations_made', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='timebankledger',
            name='transaction_type',
            field=models.CharField(choices=[('service_credit', 'Service Credit'), ('service_debit', 'Service Debit'), ('community_donation', 'Community Donation'), ('community_request', 'Community Request'), ('request_credit', 'Request Credit'), ('request_debit', 'Request Debit'), ('application_credit', 'Application Approval Credit'), ('user_donation', 'User Donation')], max_length=20),
        ),
    ]
