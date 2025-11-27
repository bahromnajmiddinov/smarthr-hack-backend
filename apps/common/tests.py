from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


class OpenAPISchemaTests(TestCase):
	def test_schema_contains_expected_tags_and_paths(self):
		"""Generate the OpenAPI schema and assert basic docs structure."""
		User = get_user_model()
		user = User.objects.create_user(username='specuser', email='spec@example.com', password='secret')

		client = APIClient()
		# force authenticate to bypass JWT/session since default permission is IsAuthenticated
		client.force_authenticate(user=user)

		resp = client.get('/api/schema/')
		self.assertEqual(resp.status_code, 200)

		data = resp.json()

		# Check tags are present and include application groupings
		tag_names = {t.get('name') for t in data.get('tags', [])}
		for expected in ('Accounts', 'Applications', 'Interviews', 'Jobs', 'Profiles', 'Analytics'):
			self.assertIn(expected, tag_names)

		# Check a few representative paths exist
		paths = data.get('paths', {})
		self.assertIn('/api/auth/register/', paths)
		self.assertIn('/api/applications/apply/', paths)
		self.assertIn('/api/interviews/', paths)
		self.assertIn('/api/jobs/', paths)
		self.assertIn('/api/profiles/me/', paths)
		self.assertIn('/api/analytics/dashboard/', paths)
