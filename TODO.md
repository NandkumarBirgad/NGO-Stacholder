# TODO: Implement role-based login flow and dashboards

1. Edit app.py:
   - Modify /login route to remove role validation.
   - Add /select_role GET and POST routes for role selection after login.
   - Add routes /dashboard/donor, /dashboard/volunteer, /dashboard/beneficiary for role-specific dashboards.
   - Adjust /dashboard route to redirect or serve accordingly.

2. Edit template/login.html:
   - Remove role selection buttons and hidden role input.

3. Create new template select_role.html:
   - Role selection UI for donor, volunteer, beneficiary.

4. Create role-specific dashboard templates (optional):
   - donor_dashboard.html
   - volunteer_dashboard.html
   - beneficiary_dashboard.html
   or adapt existing dashboard.html with role-based dynamic content.

5. Testing the full flow:
   - Register new user with role.
   - Login user with email/password.
   - Show role selection page.
   - Redirect to correct role-based dashboard according to selection.
   - Verify session management and logout.

6. Cleanup and documentation.
