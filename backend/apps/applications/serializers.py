"""Serializers for applications app."""

from rest_framework import serializers

from apps.accounts.serializers import InternalUserSerializer

from .models import (
    Application,
    ApplicationEvent,
    CandidateNote,
    Tag,
    TalentPool,
)


class ApplicationEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()
    from_stage_name = serializers.CharField(
        source='from_stage.name', default=None, read_only=True,
    )
    to_stage_name = serializers.CharField(
        source='to_stage.name', default=None, read_only=True,
    )

    class Meta:
        model = ApplicationEvent
        fields = [
            'id', 'event_type', 'actor_name',
            'from_stage_name', 'to_stage_name',
            'metadata', 'created_at',
        ]

    def get_actor_name(self, obj):
        if obj.actor:
            return obj.actor.get_full_name() or obj.actor.email
        return 'System'


class CandidateApplicationListSerializer(serializers.ModelSerializer):
    """Application list for candidates — minimal info."""

    requisition_title = serializers.CharField(
        source='requisition.title', read_only=True,
    )
    department = serializers.CharField(
        source='requisition.department.name', read_only=True,
    )
    current_stage_name = serializers.CharField(
        source='current_stage.name', default=None, read_only=True,
    )

    class Meta:
        model = Application
        fields = [
            'id', 'application_id', 'requisition_title', 'department',
            'status', 'current_stage_name', 'applied_at',
        ]


class CandidateApplicationDetailSerializer(serializers.ModelSerializer):
    """Application detail for candidates — includes timeline."""

    requisition_title = serializers.CharField(
        source='requisition.title', read_only=True,
    )
    department = serializers.CharField(
        source='requisition.department.name', read_only=True,
    )
    location = serializers.CharField(
        source='requisition.location.name', read_only=True,
    )
    current_stage_name = serializers.CharField(
        source='current_stage.name', default=None, read_only=True,
    )
    events = ApplicationEventSerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'application_id', 'requisition_title',
            'department', 'location',
            'status', 'current_stage_name',
            'cover_letter', 'screening_responses',
            'applied_at', 'withdrawn_at', 'events',
        ]


class ApplicationCreateSerializer(serializers.Serializer):
    """Input for creating an application."""

    requisition_id = serializers.UUIDField()
    cover_letter = serializers.CharField(
        max_length=5000, required=False, allow_blank=True, default='',
    )
    screening_responses = serializers.DictField(required=False, default=dict)
    source = serializers.ChoiceField(
        choices=Application.SOURCE_CHOICES,
        default='career_site',
    )


class InternalApplicationListSerializer(serializers.ModelSerializer):
    """Application list for internal dashboard."""

    candidate_name = serializers.SerializerMethodField()
    candidate_email = serializers.EmailField(
        source='candidate.user.email', read_only=True,
    )
    requisition_title = serializers.CharField(
        source='requisition.title', read_only=True,
    )
    current_stage_name = serializers.CharField(
        source='current_stage.name', default=None, read_only=True,
    )

    class Meta:
        model = Application
        fields = [
            'id', 'application_id', 'candidate_name', 'candidate_email',
            'requisition_title', 'status', 'current_stage_name',
            'source', 'is_starred', 'applied_at',
        ]

    def get_candidate_name(self, obj):
        return obj.candidate.user.get_full_name()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color']


class CandidateNoteSerializer(serializers.ModelSerializer):
    author = InternalUserSerializer(read_only=True)

    class Meta:
        model = CandidateNote
        fields = ['id', 'author', 'body', 'is_private', 'created_at']


class CandidateNoteCreateSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=5000)
    is_private = serializers.BooleanField(default=False)


class PipelineApplicationSerializer(serializers.ModelSerializer):
    """Compact serializer for pipeline board cards."""

    candidate_name = serializers.SerializerMethodField()
    candidate_email = serializers.EmailField(
        source='candidate.user.email', read_only=True,
    )
    current_stage_name = serializers.CharField(
        source='current_stage.name', default=None, read_only=True,
    )

    class Meta:
        model = Application
        fields = [
            'id', 'application_id', 'candidate_name', 'candidate_email',
            'status', 'current_stage_name', 'is_starred', 'applied_at',
        ]

    def get_candidate_name(self, obj):
        return obj.candidate.user.get_full_name()


class PipelineStageSerializer(serializers.Serializer):
    """Stage with nested applications for the Kanban board."""

    id = serializers.UUIDField()
    name = serializers.CharField()
    order = serializers.IntegerField()
    stage_type = serializers.CharField()
    application_count = serializers.IntegerField()
    applications = PipelineApplicationSerializer(many=True)


class InternalApplicationDetailSerializer(serializers.ModelSerializer):
    """Full detail for a single application (internal view)."""

    candidate_name = serializers.SerializerMethodField()
    candidate_email = serializers.EmailField(
        source='candidate.user.email', read_only=True,
    )
    requisition_title = serializers.CharField(
        source='requisition.title', read_only=True,
    )
    requisition_id_display = serializers.CharField(
        source='requisition.requisition_id', read_only=True,
    )
    department = serializers.CharField(
        source='requisition.department.name', read_only=True,
    )
    current_stage_name = serializers.CharField(
        source='current_stage.name', default=None, read_only=True,
    )
    events = ApplicationEventSerializer(many=True, read_only=True)
    notes = CandidateNoteSerializer(many=True, read_only=True)
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            'id', 'application_id', 'candidate_name', 'candidate_email',
            'requisition_title', 'requisition_id_display', 'department',
            'status', 'current_stage_name',
            'source', 'cover_letter', 'screening_responses',
            'resume_snapshot', 'is_starred',
            'rejection_reason', 'rejected_at',
            'hired_at', 'withdrawn_at', 'applied_at',
            'events', 'notes', 'tags',
        ]

    def get_candidate_name(self, obj):
        return obj.candidate.user.get_full_name()

    def get_tags(self, obj):
        return TagSerializer(
            [at.tag for at in obj.application_tags.all()],
            many=True,
        ).data


class MoveToStageSerializer(serializers.Serializer):
    stage_id = serializers.UUIDField()


class BulkActionSerializer(serializers.Serializer):
    application_ids = serializers.ListField(
        child=serializers.UUIDField(), min_length=1,
    )


class BulkRejectSerializer(BulkActionSerializer):
    reason = serializers.CharField(max_length=200, required=False, default='')


class AddTagSerializer(serializers.Serializer):
    tag_name = serializers.CharField(max_length=50)


class TalentPoolSerializer(serializers.ModelSerializer):
    """Talent pool list serializer."""

    owner_name = serializers.SerializerMethodField()
    candidate_count = serializers.SerializerMethodField()

    class Meta:
        model = TalentPool
        fields = [
            'id', 'name', 'description', 'owner', 'owner_name',
            'is_dynamic', 'candidate_count', 'created_at', 'updated_at',
        ]

    def get_owner_name(self, obj):
        if obj.owner and obj.owner.user:
            return obj.owner.user.get_full_name()
        return None

    def get_candidate_count(self, obj):
        return obj.candidates.count()


class TalentPoolDetailSerializer(TalentPoolSerializer):
    """Talent pool detail with candidate list."""

    candidates = serializers.SerializerMethodField()

    class Meta(TalentPoolSerializer.Meta):
        fields = TalentPoolSerializer.Meta.fields + [
            'search_criteria', 'candidates',
        ]

    def get_candidates(self, obj):
        from apps.accounts.serializers import CandidateProfileListSerializer

        return CandidateProfileListSerializer(
            obj.candidates.all(), many=True,
        ).data


class TalentPoolCreateSerializer(serializers.Serializer):
    """Input for creating a talent pool."""

    name = serializers.CharField(max_length=200)
    description = serializers.CharField(
        max_length=1000, required=False, allow_blank=True, default='',
    )
    is_dynamic = serializers.BooleanField(default=False)
    search_criteria = serializers.DictField(required=False, default=dict)


class TalentPoolUpdateSerializer(serializers.Serializer):
    """Input for updating a talent pool."""

    name = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(
        max_length=1000, required=False, allow_blank=True,
    )
    is_dynamic = serializers.BooleanField(required=False)
    search_criteria = serializers.DictField(required=False)


class TalentPoolAddCandidatesSerializer(serializers.Serializer):
    """Input for adding candidates to a pool."""

    candidate_ids = serializers.ListField(
        child=serializers.UUIDField(), min_length=1,
    )


class TalentPoolRemoveCandidatesSerializer(serializers.Serializer):
    """Input for removing candidates from a pool."""

    candidate_ids = serializers.ListField(
        child=serializers.UUIDField(), min_length=1,
    )
