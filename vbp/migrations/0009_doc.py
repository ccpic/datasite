# Generated by Django 3.0.8 on 2021-02-20 03:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vbp', '0008_bid_bid_spec'),
    ]

    operations = [
        migrations.CreateModel(
            name='Doc',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='doc_file')),
            ],
        ),
    ]
