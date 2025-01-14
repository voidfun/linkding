from django.test import TestCase
from django.urls import reverse

from bookmarks.models import build_tag_string
from bookmarks.tests.helpers import BookmarkFactoryMixin


class BookmarkEditViewTestCase(TestCase, BookmarkFactoryMixin):

    def setUp(self) -> None:
        user = self.get_or_create_test_user()
        self.client.force_login(user)

    def create_form_data(self, overrides=None):
        if overrides is None:
            overrides = {}
        form_data = {
            'url': 'http://example.com/edited',
            'tag_string': 'editedtag1 editedtag2',
            'title': 'edited title',
            'description': 'edited description',
            'return_url': reverse('bookmarks:index'),
        }
        return {**form_data, **overrides}

    def test_should_edit_bookmark(self):
        bookmark = self.setup_bookmark()
        form_data = self.create_form_data({'id': bookmark.id})

        self.client.post(reverse('bookmarks:edit', args=[bookmark.id]), form_data)

        bookmark.refresh_from_db()

        self.assertEqual(bookmark.owner, self.user)
        self.assertEqual(bookmark.url, form_data['url'])
        self.assertEqual(bookmark.title, form_data['title'])
        self.assertEqual(bookmark.description, form_data['description'])
        self.assertEqual(bookmark.tags.count(), 2)
        self.assertEqual(bookmark.tags.all()[0].name, 'editedtag1')
        self.assertEqual(bookmark.tags.all()[1].name, 'editedtag2')

    def test_should_use_bookmark_index_as_default_return_url(self):
        bookmark = self.setup_bookmark()

        response = self.client.get(reverse('bookmarks:edit', args=[bookmark.id]))
        html = response.content.decode()

        self.assertInHTML(
            '<input type="hidden" name="return_url" value="{0}" '
            'id="id_return_url">'.format(reverse('bookmarks:index')),
            html)

    def test_should_prefill_bookmark_form_fields(self):
        tag1 = self.setup_tag()
        tag2 = self.setup_tag()
        bookmark = self.setup_bookmark(tags=[tag1, tag2], title='edited title', description='edited description')

        response = self.client.get(reverse('bookmarks:edit', args=[bookmark.id]))
        html = response.content.decode()

        self.assertInHTML('<input type="text" name="url" '
                          'value="{0}" placeholder=" " '
                          'autofocus class="form-input" required '
                          'id="id_url">'.format(bookmark.url),
                          html)

        tag_string = build_tag_string(bookmark.tag_names, ' ')
        self.assertInHTML('<input type="text" name="tag_string" '
                          'value="{0}" autocomplete="off" '
                          'class="form-input" '
                          'id="id_tag_string">'.format(tag_string),
                          html)

        self.assertInHTML('<input type="text" name="title" maxlength="512" '
                          'autocomplete="off" class="form-input" '
                          'value="{0}" id="id_title">'.format(bookmark.title),
                          html)

        self.assertInHTML('<textarea name="description" cols="40" rows="4" class="form-input" id="id_description">{0}'
                          '</textarea>'.format(bookmark.description),
                          html)

    def test_should_prefill_return_url_from_url_parameter(self):
        bookmark = self.setup_bookmark()

        response = self.client.get(reverse('bookmarks:edit', args=[bookmark.id]) + '?return_url=/test-return-url')
        html = response.content.decode()

        self.assertInHTML('<input type="hidden" name="return_url" value="/test-return-url" id="id_return_url">', html)

    def test_should_redirect_to_return_url(self):
        bookmark = self.setup_bookmark()
        form_data = self.create_form_data({'return_url': reverse('bookmarks:close')})

        response = self.client.post(reverse('bookmarks:edit', args=[bookmark.id]), form_data)

        self.assertRedirects(response, form_data['return_url'])
