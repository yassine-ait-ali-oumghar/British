from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.core.models import Employee

class UserManagementTestCase(TestCase):
    def setUp(self):
        self.client = Client(HTTP_HOST='127.0.0.1')
        self.existing_user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='Password123!'
        )
        self.admin_user = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='AdminPassword123!'
        )

    def test_valid_signup_creates_simple_user_and_redirects_to_home(self):
        """Verify valid signup creates User & simple profile (USER, not team member) and redirects to homepage."""
        response = self.client.post('/accounts/signup/', {
            'username': 'newuniqueuser',
            'email': 'newunique@example.com',
            'password1': 'StrongPassword123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

        # Check DB User creation
        user_exists = User.objects.filter(username='newuniqueuser').exists()
        self.assertTrue(user_exists)

        user = User.objects.get(username='newuniqueuser')
        # Check DB Employee profile creation
        self.assertTrue(hasattr(user, 'employee_profile'))
        self.assertEqual(user.employee_profile.role, 'USER')
        self.assertFalse(user.employee_profile.is_team_member)

    def test_simple_user_cannot_access_employee_dashboard(self):
        """Verify simple user is denied access to employee dashboard."""
        self.client.login(username='existinguser', password='Password123!')
        response = self.client.get('/employee/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/employee/access-denied/', response.url)

    def test_simple_user_does_not_see_admin_or_employee_menu(self):
        """Verify simple user does not see Administration or Espace Employé in header dropdown."""
        self.client.login(username='existinguser', password='Password123!')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Dashboard ERP Admin')
        self.assertNotContains(response, 'Mon Tableau de Bord')

    def test_admin_can_promote_user_to_team_and_grant_employee_access(self):
        """Verify admin can promote a user to team in dashboard_users and user can then access employee portal."""
        simple_user = self.existing_user
        emp = simple_user.employee_profile
        self.assertFalse(emp.is_team_member)

        # Login as Admin
        self.client.login(username='adminuser', password='AdminPassword123!')

        # Promote user
        res_promote = self.client.post('/dashboard/users/', {
            'action': 'add_to_team',
            'employee_id': emp.id,
            'position': 'Styliste Senior',
            'department': 'Salon',
            'role': 'EMPLOYEE'
        })
        self.assertEqual(res_promote.status_code, 302)

        emp.refresh_from_db()
        self.assertTrue(emp.is_team_member)
        self.assertEqual(emp.role, 'EMPLOYEE')
        self.assertEqual(emp.position, 'Styliste Senior')

        # Logout admin, login promoted user
        self.client.logout()
        self.client.login(username='existinguser', password='Password123!')
        res_emp = self.client.get('/employee/dashboard/')
        self.assertEqual(res_emp.status_code, 200)

    def test_admin_can_delete_user(self):
        """Verify admin can delete a user account from dashboard_users."""
        target_user = User.objects.create_user(
            username='user_to_delete',
            email='delete_me@example.com',
            password='Password123!'
        )
        emp_id = target_user.employee_profile.id

        self.client.login(username='adminuser', password='AdminPassword123!')
        res_delete = self.client.post('/dashboard/users/', {
            'action': 'delete_user',
            'employee_id': emp_id
        })
        self.assertEqual(res_delete.status_code, 302)
        self.assertFalse(User.objects.filter(username='user_to_delete').exists())

    def test_similar_username_creates_account_with_auto_suffix(self):
        """Verify signing up with an existing username automatically appends a suffix (e.g. existinguser1) without error."""
        res_dup_user = self.client.post('/accounts/signup/', {
            'username': 'existinguser',
            'email': 'different@example.com',
            'password1': 'StrongPassword123!'
        })
        self.assertEqual(res_dup_user.status_code, 302)
        self.assertEqual(res_dup_user.url, '/')
        
        # Verify user was created with suffix
        user = User.objects.get(email='different@example.com')
        self.assertEqual(user.username, 'existinguser1')

    def test_signup_validation_errors_displayed_and_values_preserved(self):
        """Verify validation errors (short password, duplicate email) are displayed in HTML."""
        # Short password
        res_short_pass = self.client.post('/accounts/signup/', {
            'username': 'validuser',
            'email': 'validuser@example.com',
            'password1': '123'
        })
        self.assertEqual(res_short_pass.status_code, 200)
        self.assertContains(res_short_pass, 'This password is too short')
        self.assertContains(res_short_pass, 'value="validuser"')
        self.assertFalse(User.objects.filter(username='validuser').exists())

        # Duplicate email
        res_dup_email = self.client.post('/accounts/signup/', {
            'username': 'differentuser',
            'email': 'existing@example.com',
            'password1': 'StrongPassword123!'
        })
        self.assertEqual(res_dup_email.status_code, 200)
        self.assertContains(res_dup_email, 'existe déjà')
