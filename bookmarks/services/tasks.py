import logging
import threading

import waybackpy
from background_task import background
from django.conf import settings
from django.contrib.auth import get_user_model
from waybackpy.exceptions import WaybackError

from bookmarks.models import Bookmark

logger = logging.getLogger(__name__)


def do_archive(bookmark: Bookmark, wayback):
    try:
        archive = wayback.save()
    except WaybackError as error:
        logger.exception(f'Error creating web archive link for bookmark: {bookmark}...', exc_info=error)
        raise

    bookmark.web_archive_snapshot_url = archive.archive_url
    bookmark.save()
    logger.debug(f'Successfully created web archive link for bookmark: {bookmark}...')


def create_web_archive_snapshot(bookmark_id: int, force_update: bool):
    try:
        bookmark = Bookmark.objects.get(id=bookmark_id)
    except Bookmark.DoesNotExist:
        return

    # Skip if snapshot exists and update is not explicitly requested
    if bookmark.web_archive_snapshot_url and not force_update:
        return

    logger.debug(f'Create web archive link for bookmark: {bookmark}...')

    wayback = waybackpy.Url(bookmark.url)

    threading.Thread(target=do_archive, args=(bookmark, wayback)).start()



def schedule_bookmarks_without_snapshots(user_id: int):
    if not settings.LD_ENABLE_AUTO_WEBARCHIVE:
        logger.debug("Not auto schedule_bookmarks_without_snapshots")
        return
    logger.debug("Auto schedule_bookmarks_without_snapshots")
    user = get_user_model().objects.get(id=user_id)
    bookmarks_without_snapshots = Bookmark.objects.filter(web_archive_snapshot_url__exact='', owner=user)

    for bookmark in bookmarks_without_snapshots:
        create_web_archive_snapshot(bookmark.id, False)
