"""Initial migration for the scoring app."""

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('applications', '0004_remove_application_unique_candidate_requisition_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CandidateScore',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('profile_score', models.IntegerField(blank=True, null=True)),
                ('interview_score', models.IntegerField(blank=True, null=True)),
                ('assessment_score', models.IntegerField(blank=True, null=True)),
                ('final_score', models.IntegerField(blank=True, null=True)),
                ('profile_breakdown', models.JSONField(blank=True, default=dict)),
                ('interview_breakdown', models.JSONField(blank=True, default=dict)),
                ('assessment_breakdown', models.JSONField(blank=True, default=dict)),
                ('meets_required_criteria', models.BooleanField(default=True)),
                ('scored_at', models.DateTimeField(auto_now=True)),
                ('scoring_version', models.CharField(default='1.0', max_length=10)),
                ('application', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='candidate_score',
                    to='applications.application',
                )),
            ],
            options={
                'db_table': 'scoring_candidate_score',
            },
        ),
        migrations.AddIndex(
            model_name='candidatescore',
            index=models.Index(fields=['application'], name='scoring_application_idx'),
        ),
        migrations.AddIndex(
            model_name='candidatescore',
            index=models.Index(fields=['final_score'], name='scoring_final_score_idx'),
        ),
    ]
