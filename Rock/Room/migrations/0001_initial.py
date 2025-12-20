from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('room_code', models.CharField(max_length=6, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('host', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('password', models.CharField(max_length=128)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('is_superuser', models.BooleanField(default=False)),
                ('username', models.CharField(max_length=150, unique=True)),
                ('first_name', models.CharField(max_length=150, blank=True)),
                ('last_name', models.CharField(max_length=150, blank=True)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('current_room', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Room.room')),
                ('groups', models.ManyToManyField(blank=True, to='auth.group')),
                ('user_permissions', models.ManyToManyField(blank=True, to='auth.permission')),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='Song',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=250)),
                ('video_id', models.CharField(max_length=50)),
                ('thumbnail', models.URLField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('played_at', models.DateTimeField(blank=True, null=True)),
                ('added_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Room.room')),
            ],
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Room.room')),
                ('song', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='Room.song')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('song', 'user', 'room')},
            },
        ),
    ]
