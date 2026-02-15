"""Compliance serializers."""

from rest_framework import serializers

from .models import AnonymizationRecord, AuditLog, ConsentRecord, DataRetentionPolicy, EEOData


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit log entries."""

    actor_email = serializers.EmailField(source='actor.email', read_only=True)
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'actor',
            'actor_email',
            'actor_name',
            'actor_ip',
            'action',
            'resource_type',
            'resource_id',
            'changes',
            'metadata',
            'timestamp',
        ]
        read_only_fields = fields

    def get_actor_name(self, obj):
        if obj.actor:
            return obj.actor.get_full_name()
        return 'System'


class ConsentRecordSerializer(serializers.ModelSerializer):
    """Serializer for consent records."""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    consent_type_display = serializers.CharField(
        source='get_consent_type_display', read_only=True
    )
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = ConsentRecord
        fields = [
            'id',
            'user',
            'user_email',
            'consent_type',
            'consent_type_display',
            'given_at',
            'withdrawn_at',
            'is_active',
            'ip_address',
            'user_agent',
        ]
        read_only_fields = [
            'id',
            'user',
            'user_email',
            'consent_type_display',
            'given_at',
            'withdrawn_at',
            'is_active',
        ]


class AnonymizationRecordSerializer(serializers.ModelSerializer):
    """Serializer for anonymization records."""

    anonymized_by_email = serializers.EmailField(
        source='anonymized_by.email', read_only=True, allow_null=True
    )

    class Meta:
        model = AnonymizationRecord
        fields = [
            'id',
            'candidate_id',
            'candidate_email_hash',
            'anonymized_at',
            'anonymized_by',
            'anonymized_by_email',
            'reason',
            'applications_count',
            'metadata',
        ]
        read_only_fields = fields


class DataRetentionPolicySerializer(serializers.ModelSerializer):
    """Serializer for data retention policies."""

    data_type_display = serializers.CharField(source='get_data_type_display', read_only=True)
    total_retention_days = serializers.SerializerMethodField()

    class Meta:
        model = DataRetentionPolicy
        fields = [
            'id',
            'data_type',
            'data_type_display',
            'retention_days',
            'grace_period_days',
            'total_retention_days',
            'is_active',
            'description',
            'last_executed',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_executed']

    def get_total_retention_days(self, obj):
        return obj.retention_days + obj.grace_period_days


class EEODataSerializer(serializers.ModelSerializer):
    """
    Serializer for EEO data.

    CRITICAL: This should ONLY be used for candidate self-service.
    NEVER expose this to hiring team or internal users.
    """

    candidate_email = serializers.EmailField(source='candidate.user.email', read_only=True)

    class Meta:
        model = EEOData
        fields = [
            'id',
            'candidate',
            'candidate_email',
            'gender',
            'race_ethnicity',
            'veteran_status',
            'disability_status',
            'consent_given',
            'collected_at',
        ]
        read_only_fields = ['id', 'candidate', 'candidate_email', 'collected_at']


class EEODataSubmitSerializer(serializers.Serializer):
    """Serializer for submitting EEO data."""

    gender = serializers.CharField(max_length=100, required=False, allow_blank=True)
    race_ethnicity = serializers.CharField(max_length=200, required=False, allow_blank=True)
    veteran_status = serializers.CharField(max_length=100, required=False, allow_blank=True)
    disability_status = serializers.CharField(max_length=100, required=False, allow_blank=True)
    consent_given = serializers.BooleanField(default=True)


class ConsentSubmitSerializer(serializers.Serializer):
    """Serializer for submitting consent."""

    consent_type = serializers.ChoiceField(choices=ConsentRecord.CONSENT_TYPES)
    ip_address = serializers.IPAddressField(required=False, allow_null=True)
    user_agent = serializers.CharField(required=False, allow_blank=True)


class ConsentWithdrawSerializer(serializers.Serializer):
    """Serializer for withdrawing consent."""

    consent_type = serializers.ChoiceField(choices=ConsentRecord.CONSENT_TYPES)


class DataExportRequestSerializer(serializers.Serializer):
    """Serializer for requesting data export."""

    email = serializers.BooleanField(
        default=False, help_text='Send export via email instead of returning JSON'
    )


class AnonymizationRequestSerializer(serializers.Serializer):
    """Serializer for requesting anonymization."""

    reason = serializers.CharField(
        max_length=200,
        required=False,
        default='User-requested data deletion (GDPR Right to Erasure)',
    )
    confirm = serializers.BooleanField(
        required=True, help_text='Must be true to confirm irreversible anonymization'
    )

    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError(
                'You must confirm that you understand this action is irreversible.'
            )
        return value


class EEOReportRequestSerializer(serializers.Serializer):
    """Serializer for requesting EEO report."""

    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    department_id = serializers.UUIDField(required=False, allow_null=True)


class AdverseImpactAnalysisRequestSerializer(serializers.Serializer):
    """Serializer for requesting adverse impact analysis."""

    requisition_id = serializers.UUIDField(required=False, allow_null=True)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)


class AuditLogFilterSerializer(serializers.Serializer):
    """Serializer for filtering audit logs."""

    actor_id = serializers.UUIDField(required=False)
    action = serializers.CharField(required=False)
    resource_type = serializers.CharField(required=False)
    resource_id = serializers.CharField(required=False)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
