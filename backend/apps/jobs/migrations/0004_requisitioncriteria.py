"""Migration to add RequisitionCriteria model."""

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0003_change_currency_to_zar'),
    ]

    operations = [
        migrations.CreateModel(
            name='RequisitionCriteria',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('criterion_type', models.CharField(
                    choices=[
                        ('skill', 'Skill'),
                        ('experience_years', 'Years of Experience'),
                        ('education', 'Education Level'),
                        ('job_title', 'Job Title'),
                    ],
                    db_index=True,
                    max_length=20,
                )),
                ('value', models.CharField(
                    blank=True,
                    help_text='Skill name, degree keyword, or job title keyword.',
                    max_length=200,
                )),
                ('weight', models.PositiveIntegerField(
                    default=10,
                    help_text='Relative weight 1\u2013100.',
                )),
                ('is_required', models.BooleanField(
                    default=False,
                    help_text='If true and unmet, caps final score at 40.',
                )),
                ('min_proficiency', models.CharField(
                    blank=True,
                    choices=[
                        ('beginner', 'Beginner'),
                        ('intermediate', 'Intermediate'),
                        ('advanced', 'Advanced'),
                        ('expert', 'Expert'),
                    ],
                    help_text='Minimum proficiency level for skill criteria.',
                    max_length=20,
                )),
                ('min_years', models.PositiveIntegerField(
                    blank=True,
                    help_text='Minimum years for experience_years criteria.',
                    null=True,
                )),
                ('order', models.PositiveIntegerField(default=0)),
                ('requisition', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='criteria',
                    to='jobs.requisition',
                )),
            ],
            options={
                'db_table': 'jobs_requisition_criteria',
                'ordering': ['requisition', 'order'],
            },
        ),
        migrations.AddIndex(
            model_name='requisitioncriteria',
            index=models.Index(
                fields=['requisition', 'criterion_type'],
                name='jobs_req_criteria_type_idx',
            ),
        ),
    ]
