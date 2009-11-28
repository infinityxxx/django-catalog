# -*- coding: utf-8 -*-
from django.db import models
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.conf import settings
from catalog.fields import RelatedField
from catalog import settings as catalog_settings
from django.core.exceptions import ObjectDoesNotExist,ImproperlyConfigured

if catalog_settings.CATALOG_MPTT:
    import mptt
else:
    from catalog import dummy_mptt as mptt


class Base(models.Model):
    class Meta:
        abstract = True

    tree = generic.GenericRelation('TreeItem')
    tree_id = models.IntegerField(editable=False, null=True)
    exclude_children = []
    
    def save(self, *args, **kwds):
        save_tree_id = kwds.pop('save_tree_id', True)
        if save_tree_id:
            self.tree_id = self.tree.get().id
        return super(Base, self).save(*args, **kwds)
    save.alters_data = True
    
    def delete(self, *args, **kwds):
        super(Base, self).delete(*args, **kwds)
    delete.alters_data = True


class TreeItemManager(models.Manager):

    def json(self, treeitem_id):
        '''Returns treeitem by it's id, if "root" given returns None'''
        if treeitem_id == 'root':
            return None
        else:
            return TreeItem.objects.get(id=treeitem_id)

    def json_children(self, parent):
        '''
        Returns children treeitems by their parent id.
        If 'root' given returns root treeitems
        '''
        if parent == 'root':
            parent = None
        return TreeItem.objects.filter(parent=parent)

    def linked(self, treeid):
        if treeid == 'root':
            return []
        treeitem = TreeItem.objects.get(id=treeid)
        if treeitem.content_type.model == 'section':
            related_ids = treeitem.content_object.items.values_list('id', flat=True)
            item_ct = ContentType.objects.get_for_model(Item)
            related = TreeItem.objects.filter(content_type=item_ct, object_id__in=related_ids)
            return related 


class TreeItem(models.Model):
    class Meta:
        verbose_name = u'Элемент каталога'
        verbose_name_plural = u'Элементы каталога'
        if catalog_settings.CATALOG_MPTT:
            ordering = ['tree_id', 'lft']
            if catalog_settings.EXTRA_ORDER:
                # insert order first
                ordering[0:0] = ['order']
        else:
            ordering = ['id']

    parent = models.ForeignKey('self', related_name='children',
        verbose_name=u'Родительский', null=True, blank=True, editable=False)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    if catalog_settings.EXTRA_ORDER:
        order = models.IntegerField(null=True)
    
    manager = TreeItemManager()
    
    def get_absolute_url(self):
        return self.get_absolute_url_undecorated()
    
    def delete(self, *args, **kwds):
        self.content_object.delete()
        super(TreeItem, self).delete(*args, **kwds)
    delete.alters_data = True
    
    def save(self, *args, **kwds):
        if catalog_settings.CATALOG_MPTT and catalog_settings.EXTRA_ORDER:
            if self.tree_id is None:
                self.order = 0
            else:
                self.order = self.lft * self.tree_id
            super(TreeItem, self).save(*args, **kwds)
        else:
            return super(TreeItem, self).save(*args, **kwds)
    save.alters_data = True

    def get_level(self):
        ''' need to override this, because when we turn mptt off,
            level attr will clash with level method
        '''
        return self.level

    def get_absolute_url_undecorated(self):
        return ('tree', (), {'item_id': self.id, 'slug': self.slug()})
    
    def slug(self):
        try:
            return self.content_object.slug
        except:
            return u'slug'

try:
    mptt.register(TreeItem, tree_manager_attr='objects')
except mptt.AlreadyRegistered:
    pass

# HACK: import models by their names for convenient usage
for model_name, admin_name in catalog_settings.CATALOG_CONNECTED_MODELS:
    module, model = model_name.rsplit('.', 1)
    exec('from %s import %s' % (module, model))

# must be at bottom, otherwies breaks imports
from catalog.admin.utils import get_connected_models

def filtered_children_factory(model_name):
    def func(self):
        return self.children.filter(content_type__model=model_name)
    return func
 
for model_cls, admin_cls in get_connected_models():
    model_name = model_cls.__name__.lower()
    setattr(TreeItem, 'children_%s' % model_name, filtered_children_factory(model_name))
