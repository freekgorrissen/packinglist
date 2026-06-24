from django.test import SimpleTestCase

from packinglist.settings import _database_from_url


class DatabaseFromUrlTests(SimpleTestCase):
    def test_parses_postgres_url(self):
        config = _database_from_url(
            'postgres://packinglist:secret@db:5432/packinglist'
        )
        self.assertEqual(config['ENGINE'], 'django.db.backends.postgresql')
        self.assertEqual(config['NAME'], 'packinglist')
        self.assertEqual(config['USER'], 'packinglist')
        self.assertEqual(config['PASSWORD'], 'secret')
        self.assertEqual(config['HOST'], 'db')
        self.assertEqual(config['PORT'], 5432)

    def test_decodes_url_encoded_password(self):
        config = _database_from_url('postgres://user:p%40ss@localhost/packinglist')
        self.assertEqual(config['PASSWORD'], 'p@ss')
