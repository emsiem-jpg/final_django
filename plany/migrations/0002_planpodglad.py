# Generated by Django 5.2.1 on 2025-06-06 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plany', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlanPodglad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan_id', models.IntegerField()),
                ('plan_nazwa', models.CharField(max_length=255)),
                ('etap_nr', models.IntegerField()),
                ('etap_nazwa', models.CharField(max_length=255)),
                ('atr_nr', models.IntegerField()),
                ('atrakcja_nazwa', models.CharField(max_length=255)),
                ('planowana_data', models.DateTimeField()),
                ('czas_wizyty', models.IntegerField()),
                ('czas_dojazdu', models.IntegerField()),
            ],
            options={
                'db_table': 'v_plan_podglad',
                'managed': False,
            },
        ),
    ]
