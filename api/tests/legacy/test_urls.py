from django.urls import reverse, resolve

# Path for user-auth and oauth2_provider not tested
# as they are part of django's own libraries or third parties


class TestUrls:
    def test_get_all_positions_url(self):
        path = reverse('api:get-positions')
        assert resolve(path).view_name == 'api:get-positions'

    def test_get_one_position_url(self):
        path = reverse('api:id-positions', kwargs={'id': 1})
        assert resolve(path).view_name == 'api:id-positions'

    def test_get_all_badges_url(self):
        path = reverse('api:get-badges')
        assert resolve(path).view_name == 'api:get-badges'

    def test_get_one_badge_url(self):
        path = reverse('api:id-badges', kwargs={'id': 1})
        assert resolve(path).view_name == 'api:id-badges'

    def test_get_all_venues_url(self):
        path = reverse('api:get-venues')
        assert resolve(path).view_name == 'api:get-venues'

    def test_get_one_venue_url(self):
        path = reverse('api:id-venues', kwargs={'id': 1})
        assert resolve(path).view_name == 'api:id-venues'

    def test_get_all_profiles_url(self):
        path = reverse('api:get-profiles')
        assert resolve(path).view_name == 'api:get-profiles'

    def test_get_one_profile_url(self):
        path = reverse('api:id-profiles', kwargs={'id': 1})
        assert resolve(path).view_name == 'api:id-profiles'

    def test_get_all_shifts_url(self):
        path = reverse('api:get-shifts')
        assert resolve(path).view_name == 'api:get-shifts'

    def test_get_one_shift_url(self):
        path = reverse('api:id-shifts', kwargs={'id': 1})
        assert resolve(path).view_name == 'api:id-shifts'

    def test_get_all_favorite_lists_url(self):
        path = reverse('api:get-favlists')
        assert resolve(path).view_name == 'api:get-favlists'

    def test_get_one_favorite_list_url(self):
        path = reverse('api:id-favlists', kwargs={'id': 1})
        assert resolve(path).view_name == 'api:id-favlists'

    def test_get_all_employees_url(self):
        path = reverse('api:get-employees')
        assert resolve(path).view_name == 'api:get-employees'

    def test_get_one_employee_url(self):
        path = reverse('api:id-employees', kwargs={'id': 1})
        assert resolve(path).view_name == 'api:id-employees'

    def test_get_all_employers_url(self):
        path = reverse('api:get-employers')
        assert resolve(path).view_name == 'api:get-employers'

    def test_get_one_employer_url(self):
        path = reverse('api:id-employers', kwargs={'id': 1})
        assert resolve(path).view_name == 'api:id-employers'

    def test_get_one_user_url(self):
        path = reverse('api:id-user', kwargs={'id': 1})
        assert resolve(path).view_name == 'api:id-user'

    def test_register_url(self):
        path = reverse('api:register')
        assert resolve(path).view_name == 'api:register'

    def test_login_url(self):
        path = reverse('api:login')
        assert resolve(path).view_name == 'api:login'

    def test_register_url(self):
        path = reverse('api:register')
        assert resolve(path).view_name == 'api:register'

    def test_passwrod_reset_url(self):
        path = reverse('api:password-reset-email')
        assert resolve(path).view_name == 'api:password-reset-email'
