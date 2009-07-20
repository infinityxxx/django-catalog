from django.http import HttpResponse, HttpResponseServerError
from catalog.models import Section, Item, TreeItem
from django.contrib.auth.decorators import permission_required
from django.utils import simplejson

def get_content(parent):
    if parent == 'root':
        parent = None

    all_sections = Section.objects.filter(tree__parent=parent)
    sections = all_sections.filter(is_meta_item=False)
    metaitems = all_sections.filter(is_meta_item=True)
    items = Item.objects.filter(tree__parent=parent)
    return {'sections': sections, 'metaitems': metaitems, 'items': items}


@permission_required('catalog.add_section', login_url='/admin/')
def tree(request):
    tree = []
#    if request.method == 'POST':
    if True:
        parent = request.REQUEST.get('node', 'root')
        content = get_content(parent)

        for section in content['sections']:
            tree.append({'text': section.tree.name,
                         'id': '%d' % section.tree.id,
                         'cls': 'folder',
                         })
        for metaitem in content['metaitems']:
            tree.append({'text': metaitem.tree.name,
                         'id': '%d' % metaitem.tree.id,
                         'cls': 'folder',
                         })
        for item in content['items']:
            tree.append({'text': item.tree.name,
                         'id': '%d' % item.tree.id,
                         'leaf': 'true',
                         'cls': 'leaf',
                         })
    return HttpResponse(simplejson.encode(tree))


@permission_required('catalog.change_section', login_url='/admin/')
def list(request):
    grid = []
    if request.method == 'POST':
        parent = request.REQUEST.get('node', 'root')
        content = get_content(parent)

        for section in content['sections']:
            grid.append({'name': section.tree.name,
                         'id': '%d' % section.tree.id,
                         'cls': 'folder',
                         'type': 'section',
                         'itemid': section.id,
                         })
        for metaitem in content['metaitems']:
            grid.append({'name': metaitem.tree.name,
                         'id': '%d' % metaitem.tree.id,
                         'cls': 'folder',
                         'type': 'metaitem',
                         'itemid': metaitem.id,
                         })
        for item in content['items']:
            grid.append({'name': item.tree.name,
                         'id': '%d' % item.tree.id,
                         'cls': 'leaf',
                         'type': 'item',
                         'itemid': item.id,
                         })
    return HttpResponse(simplejson.encode({'items': grid}))

# moving tree items

def get_tree_item(node):
    if node == 'root':
        item = None
    else:
        try:
            item = TreeItem.objects.get(id=int(node))
        except TreeItem.DoesNotExist, ValueError:
            item = None
    return item

def may_move(node, parent):
    move_matrix = {
        'item': ['section', 'metaitem'],
        'metaitem': ['section'],
        'section': ['section'],
        }
    if parent is None:
        return True
    elif parent.get_type() in move_matrix[node.get_type()]:
        return True
    else:
        return False

def move_node(request):
#    if request.method == 'POST':
    if True:
        sources = request.REQUEST.get('source', '').split(',')
        target_id = int(request.REQUEST.get('target', ''))
        point = request.REQUEST.get('point', '')
        if point == 'above':
            position = 'left'
        elif point == 'below':
            position = 'right'
        else:
            position = 'last-child'

        new_parent = get_tree_item(target_id)
        # python 2.4 workaround
        move = True
        for source in sources:
            this_section = get_tree_item(source)
#            if may_move(this_section, new_parent):
#                move = move and True
#            else:
#                move = move and False

        if move:
            this_section.move_to(new_parent, position)
            return HttpResponse('OK')
        else:
            return HttpResponseServerError('Can not move')
