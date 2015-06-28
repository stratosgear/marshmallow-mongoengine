from marshmallow import ValidationError, missing
from marshmallow.fields import Field
from mongoengine import ValidationError as MongoValidationError
from mongoengine.base import get_document
# Republishing the default fields...
from marshmallow.fields import *  # flake8: noqa


# ...and add custom ones for mongoengine
class Reference(Field):
    """
    Marshmallow custom field to map with :class Mongoengine.ReferenceField:
    """

    def __init__(self, document_type_obj, *args, **kwargs):
        self.document_type_obj = document_type_obj
        super(Reference, self).__init__(*args, **kwargs)

    @property
    def document_type(self):
        if isinstance(self.document_type_obj, str):
            self.document_type_obj = get_document(self.document_type_obj)
        return self.document_type_obj

    def _deserialize(self, value):
        document_type = self.document_type
        try:
            return document_type.objects.get(pk=value)
        except document_type.DoesNotExist:
            raise ValidationError('unknown `%s` document with id `%s`' %
                                  (document_type.__name__, value))
        except MongoValidationError:
            raise ValidationError('invalid ObjectId `%s`' % value)
        return value

    def _serialize(self, value, attr, obj):
        # Only return the pk of the document for serialization
        if value is None:
            return None
        return value.pk


class GenericReference(Field):
    """
    Marshmallow custom field to map with :class Mongoengine.GenericReferenceField:
    """

    def _deserialize(self, value):
        # Cannot deserialize given we have no way knowing wich kind of
        # document is given...
        return missing

    def _serialize(self, value, attr, obj):
        # Only return the pk of the document for serialization
        if value is None:
            return None
        return value.pk


class GenericEmbeddedDocument(Field):
    """
    Dynamic embedded document
    """

    def _deserialize(self, value):
        # Cannot deserialize given we have no way knowing wich kind of
        # document is given...
        return missing

    def _serialize(self, value, attr, obj):
        # Create the schema at serialize time to be dynamic
        from marshmallow_mongoengine.schema import ModelSchema

        class NestedSchema(ModelSchema):
            class Meta:
                model = type(value)
        data, errors = NestedSchema().dump(value)
        if errors:
            raise ValidationError(errors)
        return data


class Map(Field):
    """
    Marshmallow custom field to map with :class Mongoengine.Map:
    """

    def __init__(self, mapped, **kwargs):
        self.mapped = mapped
        super(Map, self).__init__(**kwargs)

    def _serialize(self, value, attr, obj):
        total_dump = {}
        for k, v in value.items():
            data, errors = self.mapped.schema.dump(v)
            if errors:
                raise ValidationError(errors)
            total_dump[k] = data
        return total_dump

    def _deserialize(self, value):
        total_load = {}
        for k, v in value.items():
            data, errors = self.mapped.schema.load(v)
            if errors:
                raise ValidationError(errors)
            total_load[k] = data
        return total_load


class Skip(Field):
    """
    Marshmallow custom field that just ignore the current field
    """

    def _deserialize(self, value):
        return missing

    def _serialize(self, value, attr, obj):
        return missing
