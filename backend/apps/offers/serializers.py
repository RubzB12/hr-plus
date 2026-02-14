"""Serializers for offers app."""


from rest_framework import serializers

from apps.accounts.serializers import InternalUserListSerializer, JobLevelSerializer
from apps.applications.serializers import InternalApplicationListSerializer

from .models import Offer, OfferApproval, OfferNegotiationLog


class OfferSerializer(serializers.ModelSerializer):
    """Serializer for Offer model."""

    application_detail = InternalApplicationListSerializer(
        source='application', read_only=True
    )
    created_by_detail = InternalUserListSerializer(source='created_by', read_only=True)
    level_detail = JobLevelSerializer(source='level', read_only=True)

    # Decrypt salary fields for reading (convert from string to Decimal)
    base_salary_display = serializers.SerializerMethodField()
    bonus_display = serializers.SerializerMethodField()
    sign_on_bonus_display = serializers.SerializerMethodField()
    relocation_display = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id',
            'offer_id',
            'application',
            'application_detail',
            'version',
            'status',
            'title',
            'level',
            'level_detail',
            'department',
            'reporting_to',
            'base_salary_display',
            'salary_currency',
            'salary_frequency',
            'bonus_display',
            'equity',
            'sign_on_bonus_display',
            'relocation_display',
            'start_date',
            'expiration_date',
            'offer_letter_pdf',
            'notes',
            'sent_at',
            'viewed_at',
            'responded_at',
            'decline_reason',
            'esignature_envelope_id',
            'created_by',
            'created_by_detail',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'offer_id',
            'version',
            'sent_at',
            'viewed_at',
            'responded_at',
            'created_at',
            'updated_at',
        ]

    def get_base_salary_display(self, obj):
        """Convert encrypted salary to decimal for display."""
        if obj.base_salary:
            return str(obj.base_salary)  # Already decrypted by Django
        return None

    def get_bonus_display(self, obj):
        """Convert encrypted bonus to decimal for display."""
        if obj.bonus:
            return str(obj.bonus)
        return None

    def get_sign_on_bonus_display(self, obj):
        """Convert encrypted sign-on bonus to decimal for display."""
        if obj.sign_on_bonus:
            return str(obj.sign_on_bonus)
        return None

    def get_relocation_display(self, obj):
        """Convert encrypted relocation to decimal for display."""
        if obj.relocation:
            return str(obj.relocation)
        return None


class OfferCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating offers."""

    # Accept Decimal input for salary fields
    base_salary_input = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        write_only=True,
    )
    bonus_input = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True,
        write_only=True,
    )
    sign_on_bonus_input = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True,
        write_only=True,
    )
    relocation_input = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True,
        write_only=True,
    )

    class Meta:
        model = Offer
        fields = [
            'application',
            'title',
            'level',
            'department',
            'reporting_to',
            'base_salary_input',
            'salary_currency',
            'salary_frequency',
            'bonus_input',
            'equity',
            'sign_on_bonus_input',
            'relocation_input',
            'start_date',
            'expiration_date',
            'notes',
        ]


class OfferApprovalSerializer(serializers.ModelSerializer):
    """Serializer for OfferApproval model."""

    approver_detail = InternalUserListSerializer(source='approver', read_only=True)
    offer_detail = OfferSerializer(source='offer', read_only=True)

    class Meta:
        model = OfferApproval
        fields = [
            'id',
            'offer',
            'offer_detail',
            'approver',
            'approver_detail',
            'order',
            'status',
            'comments',
            'decided_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'decided_at',
            'created_at',
            'updated_at',
        ]


class OfferNegotiationLogSerializer(serializers.ModelSerializer):
    """Serializer for OfferNegotiationLog model."""

    logged_by_detail = InternalUserListSerializer(source='logged_by', read_only=True)

    class Meta:
        model = OfferNegotiationLog
        fields = [
            'id',
            'offer',
            'logged_by',
            'logged_by_detail',
            'candidate_request',
            'internal_response',
            'outcome',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CandidateOfferSerializer(serializers.ModelSerializer):
    """Serializer for candidate view of offer (limited fields)."""

    base_salary_display = serializers.SerializerMethodField()
    bonus_display = serializers.SerializerMethodField()
    sign_on_bonus_display = serializers.SerializerMethodField()
    relocation_display = serializers.SerializerMethodField()
    level_detail = JobLevelSerializer(source='level', read_only=True)

    class Meta:
        model = Offer
        fields = [
            'offer_id',
            'version',
            'status',
            'title',
            'level_detail',
            'base_salary_display',
            'salary_currency',
            'salary_frequency',
            'bonus_display',
            'equity',
            'sign_on_bonus_display',
            'relocation_display',
            'start_date',
            'expiration_date',
            'sent_at',
            'viewed_at',
        ]

    def get_base_salary_display(self, obj):
        if obj.base_salary:
            return str(obj.base_salary)
        return None

    def get_bonus_display(self, obj):
        if obj.bonus:
            return str(obj.bonus)
        return None

    def get_sign_on_bonus_display(self, obj):
        if obj.sign_on_bonus:
            return str(obj.sign_on_bonus)
        return None

    def get_relocation_display(self, obj):
        if obj.relocation:
            return str(obj.relocation)
        return None
