# Generated by Django 4.2.2 on 2023-06-13 19:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='episodic_memory',
            field=models.TextField(blank=True, null=True),
        ),
    ]
