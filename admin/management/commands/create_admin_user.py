"""
Django management command to create admin users

This command allows creating admin and super admin users
for the iSubscribe platform through the command line.

Usage:
    python manage.py create_admin_user --email admin@example.com --role admin
    python manage.py create_admin_user --email super@example.com --role super_admin
"""

from django.core.management.base import BaseCommand, CommandError
from services.supabase import supabase
import uuid
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create an admin user for the iSubscribe platform'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email address for the admin user'
        )
        
        parser.add_argument(
            '--role',
            type=str,
            choices=['admin', 'super_admin'],
            default='admin',
            help='Role for the admin user (admin or super_admin)'
        )
        
        parser.add_argument(
            '--full-name',
            type=str,
            help='Full name for the admin user'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update if user already exists'
        )
    
    def handle(self, *args, **options):
        email = options['email']
        role = options['role']
        full_name = options.get('full_name', email.split('@')[0].title())
        force = options.get('force', False)
        
        try:
            # Check if user already exists
            existing_user = supabase.table('profile').select('*').eq('email', email).execute()
            
            if existing_user.data and not force:
                self.stdout.write(
                    self.style.WARNING(f'User with email {email} already exists. Use --force to update.')
                )
                return
            
            user_data = {
                'id': str(uuid.uuid4()),
                'email': email,
                'full_name': full_name,
                'role': role,
                'onboarded': True,
                'created_at': 'now()',
                'updated_at': 'now()'
            }
            
            if existing_user.data and force:
                # Update existing user
                response = supabase.table('profile').update({
                    'role': role,
                    'full_name': full_name,
                    'updated_at': 'now()'
                }).eq('email', email).execute()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully updated admin user: {email} with role: {role}')
                )
            else:
                # Create new user
                response = supabase.table('profile').insert(user_data).execute()
                
                if response.data:
                    user_id = response.data[0]['id']
                    
                    # Create wallet for the admin user
                    wallet_data = {
                        'user': user_id,
                        'balance': 0.0,
                        'cashback_balance': 0.0,
                        'email': email
                    }
                    
                    wallet_response = supabase.table('wallet').insert(wallet_data).execute()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully created admin user: {email} with role: {role}')
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'User ID: {user_id}')
                    )
                else:
                    raise CommandError('Failed to create user')
            
            # Display user information
            self.stdout.write('\n' + '='*50)
            self.stdout.write('Admin User Details:')
            self.stdout.write('='*50)
            self.stdout.write(f'Email: {email}')
            self.stdout.write(f'Full Name: {full_name}')
            self.stdout.write(f'Role: {role}')
            self.stdout.write('='*50)
            
            # Show next steps
            self.stdout.write('\nNext Steps:')
            self.stdout.write('1. The user needs to sign up through Supabase Auth using the same email')
            self.stdout.write('2. Once signed up, they will have admin access to the platform')
            self.stdout.write('3. They can access admin endpoints using their JWT token')
            
        except Exception as e:
            logger.exception(f'Error creating admin user: {str(e)}')
            raise CommandError(f'Failed to create admin user: {str(e)}')
