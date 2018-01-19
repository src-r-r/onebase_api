#!/usr/bin/env python3
"""
This file is part of 1Base.

1Base is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

1Base is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with 1Base.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging
import copy

from datetime import (
    datetime,
)

from mongoengine import (
    Document,
    ReferenceField,
    BooleanField,
    StringField,
    DateTimeField,
    SortedListField,
    LazyReferenceField,
)

from onebase_common.log.setup import (
    configure_logging
)

configure_logging()

logger = logging.getLogger(__name__)

from onebase_api.models.mixin import (
    JsonMixin,
    TimestampOrderableMixin
)


class CommentBase(Document, JsonMixin, TimestampOrderableMixin):

    replies = SortedListField(ReferenceField('Comment'), default=list())
    timestamp = DateTimeField(required=True, default=datetime.now())

    meta = {'allow_inheritance': True, 'abstract': True, }

    @property
    def parent(self):
        return self.__class__.objects(replies__in=[self, ]).first()


class DeletedComment(CommentBase):
    """ Comment that was deleted.

    Used for comment parents and acts as a placeholder.
    """

    replies = SortedListField(ReferenceField('Comment'), default=list())
    timestamp = DateTimeField(required=True, default=datetime.now())

    def to_json(self):
        return super(DeletedComment, self).to_json()


class Comment(CommentBase):
    """ A part of a discussion. """

    author = LazyReferenceField('User', required=True)
    body = StringField(max_lenth=4096, required=True)

    meta = {'allow_inheritance': True, }

    def delete(self, *args, **kwargs):
        """ Delete a comment.

        We must override mongo's delete() in order to preserve the comment
        tree.
        """
        logger.debug("Deleting comment {}".format(self.id))
        # replace all childrens' parent with a deleted comment
        deleted = DeletedComment(replies=copy.deepcopy(self.replies),
                                 timestamp=self.timestamp)
        del self.replies
        deleted.save()
        logger.debug('placeholder comment: {}'.format(deleted))
        # get this parent's children.
        if self.parent is not None:
            for (i, reply) in enumerate(self.parent.replies):
                logger.debug("Is {} == {}".format(reply.id, self.id))
                if reply == self:
                    logger.debug('deleting comment {}'.format(self.id))
                    self.parent.replies[i] = deleted
            self.parent.save()
        # continue with mongo's delete
        super(Comment, self).delete(*args, **kwargs)


class Discussion(JsonMixin, Document):
    """ User comments pertaining to a part of 1Base.

    As with any wiki, a disagreement may arise. Discussions are there to
    allow users to state ther opinion on a particular issue.

    """

    title = StringField()
    comments = SortedListField(ReferenceField(Comment), required=True)
    is_locked = BooleanField(default=False)

    meta = {'allow_inheritance': True, }

    @property
    def starter(self):
        """ Return the comment that started the discussion. """
        return self.comments[0]
