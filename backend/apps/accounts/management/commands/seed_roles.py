"""Management command to seed default roles and permissions."""

from django.core.management.base import BaseCommand

from apps.accounts.models import Permission, Role

# Module-action pairs for each default role
DEFAULT_PERMISSIONS = {
    'Super Admin': '*',  # All permissions
    'HR Admin': {
        'accounts': ['view', 'create', 'edit', 'delete'],
        'compliance': ['view'],
        'analytics': ['view'],
        'communications': ['view', 'create', 'edit'],
    },
    'Recruiter': {
        'jobs': ['view', 'create', 'edit'],
        'applications': ['view', 'create', 'edit'],
        'candidates': ['view', 'create', 'edit'],
        'interviews': ['view', 'create', 'edit'],
        'offers': ['view', 'create', 'edit'],
        'communications': ['view', 'create', 'edit'],
        'analytics': ['view'],
    },
    'Hiring Manager': {
        'jobs': ['view', 'create', 'edit', 'approve'],
        'applications': ['view', 'edit'],
        'candidates': ['view'],
        'interviews': ['view', 'create', 'edit'],
        'offers': ['view', 'approve'],
        'analytics': ['view'],
    },
    'Interviewer': {
        'applications': ['view'],
        'candidates': ['view'],
        'interviews': ['view', 'edit'],
    },
    'Coordinator': {
        'applications': ['view'],
        'candidates': ['view'],
        'interviews': ['view', 'create', 'edit'],
        'communications': ['view', 'create'],
    },
    'Executive': {
        'jobs': ['view'],
        'applications': ['view'],
        'analytics': ['view'],
        'offers': ['view', 'approve'],
    },
    'Onboarding Specialist': {
        'onboarding': ['view', 'create', 'edit'],
        'candidates': ['view'],
        'communications': ['view', 'create'],
    },
}

ALL_MODULES = [
    'accounts', 'candidates', 'jobs', 'applications',
    'interviews', 'assessments', 'offers', 'onboarding',
    'communications', 'analytics', 'integrations', 'compliance',
]

ALL_ACTIONS = ['view', 'create', 'edit', 'delete', 'approve']


class Command(BaseCommand):
    help = 'Seed default RBAC roles and permissions'

    def handle(self, *args, **options):
        self.stdout.write('Creating permissions...')
        permissions_created = 0

        for module in ALL_MODULES:
            for action in ALL_ACTIONS:
                codename = f'{module}.{action}'
                name = f'{action.capitalize()} {module.replace("_", " ").title()}'
                _, created = Permission.objects.get_or_create(
                    codename=codename,
                    defaults={
                        'name': name,
                        'module': module,
                        'action': action,
                    },
                )
                if created:
                    permissions_created += 1

        self.stdout.write(f'  Created {permissions_created} permissions')

        self.stdout.write('Creating roles...')
        roles_created = 0
        all_perms = Permission.objects.all()

        for role_name, perm_spec in DEFAULT_PERMISSIONS.items():
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={
                    'description': f'Default {role_name} role',
                    'is_system': True,
                },
            )
            if created:
                roles_created += 1

            if perm_spec == '*':
                role.permissions.set(all_perms)
            else:
                perm_codenames = []
                for module, actions in perm_spec.items():
                    for action in actions:
                        perm_codenames.append(f'{module}.{action}')
                role.permissions.set(
                    all_perms.filter(codename__in=perm_codenames)
                )

        self.stdout.write(f'  Created {roles_created} roles')
        self.stdout.write(self.style.SUCCESS('Seed data applied successfully.'))
