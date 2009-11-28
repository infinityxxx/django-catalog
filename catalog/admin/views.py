# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.forms.models import ModelForm, modelformset_factory
from django.db import transaction
from django.http import HttpResponseRedirect, Http404
from urllib import urlencode
from catalog.admin.utils import admin_permission_required
from catalog.models import TreeItem

@transaction.commit_on_success
@admin_permission_required('catalog.add_treeitem')
def add_instance(request, model_name):
    def select_model_by_name(name):
        from catalog.admin.utils import get_connected_models
        connected_models = get_connected_models()
        model_list = [item[0].__name__.lower() for item in connected_models]
        try:
            return connected_models[model_list.index(name)][0]
        except ValueError:
            return None

    parent_tree_item = TreeItem.manager.json(request.REQUEST.get('parent', 'root'))

    model_cls = select_model_by_name(model_name)
    if model_cls is None:
        raise Http404

    instance = model_cls(name=u'%s' % model_cls._meta.verbose_name)
    instance.save(save_tree_id=False)

    tree_item = TreeItem(parent=parent_tree_item, content_object=instance)
    tree_item.save()
    
    instance.save()

    return HttpResponseRedirect('/admin/%s/%s/%d/?_popup=1'
        % (instance.__module__.rsplit('.', 2)[-2], model_name, instance.id))

def editor_redirect(request, obj_id):
    treeitem = get_object_or_404(TreeItem, id=obj_id)
    get_str = urlencode(request.GET)
    return HttpResponseRedirect('/admin/%s/%s/%s/?%s' %
        (treeitem.content_object.__module__.rsplit('.', 2)[-2], treeitem.content_type.model,
        treeitem.content_object.id, get_str))

def related_redirect(request, obj_id):
    treeitem = get_object_or_404(TreeItem, id=obj_id)
    get_str = urlencode(request.GET)
    return HttpResponseRedirect('/admin/catalog/%s/%s/rel/?%s' % (treeitem.content_type.model, treeitem.content_object.id, get_str))

def absolute_url_redirect(request, obj_id):
    treeitem = get_object_or_404(TreeItem, id=obj_id)
    get_str = urlencode(request.GET)
    return HttpResponseRedirect('%s?%s' % (treeitem.content_object.get_absolute_url(), get_str))
