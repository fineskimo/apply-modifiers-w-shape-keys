import bpy
import math
from bpy.props import *


bl_info = {
    "name": "Apply Modifiers for Object with Shape Keys",
    "description": "Allows to apply modifiers for object with Shape Keys.",
    "author": "Przemysław Bągard, Fin, Jean da Costa, Lucas Falcao",
    "blender": (2, 80, 0),
    "version": (0, 1, 2),
    "location": "3D View",
    "wiki_url": "https://github.com/lucasfalcao3d/apply-modifiers-w-shape-keys",
    "category": "Interface"
}

# Algorithm:
# - Duplicate active object as many times as the number of shape keys
# - For each copy remove all shape keys except one
# - Removing last shape does not change geometry data of object
# - Apply modifier for each copy
# - Join objects as shapes and restore shape keys names
# - Delete all duplicated object except one
# - Delete old object
# - Restore name of object and object data


def ShowMessageBox(message="", title="Message Box", icon='INFO'):
    # Simple display message utility

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def apply_modifiers(context, modifierName):
    list_names = []
    list = []
    list_shapes = []
    basename = bpy.context.object.name

    if context.object.data.shape_keys:
        list_shapes = [o for o in context.object.data.shape_keys.key_blocks]

    if(list_shapes == []):
        bpy.ops.object.modifier_apply(modifier=modifierName)
        return context.view_layer.objects.active

    list.append(context.view_layer.objects.active)

    for i in range(1, len(list_shapes)):
        bpy.ops.object.duplicate(linked=False, mode='TRANSLATION')

        list.append(context.view_layer.objects.active)

    for i, o in enumerate(list):
        context.view_layer.objects.active = o
        list_names.append(o.data.shape_keys.key_blocks[i].name)

        for j in range(i + 1, len(list))[::-1]:
            context.object.active_shape_key_index = j
            print("loop one")

            bpy.ops.object.shape_key_remove()

        for j in range(0, i):
            print("loop two")
            context.object.active_shape_key_index = 0

            bpy.ops.object.shape_key_remove()

        # last deleted shape doesn't change object shape
        context.object.active_shape_key_index = 0
        bpy.ops.object.shape_key_remove()
        print("out")

        try:
            bpy.ops.object.modifier_apply(modifier=modifierName)
            print("apply")
        except RuntimeError:
            ShowMessageBox("Modifer is disabled, skipping apply", "Report: Error ", 'ERROR')

        if i > 0:
            bpy.context.object.name = f'{basename}_{list_names[i]}'
            # time to apply modifiers
            try:
                bpy.ops.object.modifier_apply(modifier=modifierName)
                print("apply2")
            except RuntimeError:
                ShowMessageBox("Modifer is disabled, skipping apply", "Report: Error ", 'ERROR')

    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = list[0]
    list[0].select_set(True)
    bpy.ops.object.shape_key_add(from_mix=False)
    context.object.data.shape_keys.key_blocks[0].name = list_names[0]

    for i in range(1, len(list)):
        list[i].select_set(state=True)
        bpy.ops.object.join_shapes()
        list[i].select_set(state=False)
        context.object.data.shape_keys.key_blocks[i].name = list_names[i]

    bpy.ops.object.select_all(action='DESELECT')

    for o in list[1:]:
        o.select_set(True)

    bpy.ops.object.delete(use_global=False)
    context.view_layer.objects.active = list[0]
    context.view_layer.objects.active.select_set(state=True)
    return context.view_layer.objects.active


class AWS_OT_operator(bpy.types.Operator):
    bl_idname = "aws.operator"
    bl_label = "Apply Modifiers w/Shape Keys"
    bl_description = ("Apply Modifiers for objects with Shape Keys")
    bl_options = {'UNDO'}

    def item_list(self, context):
        return [(modifier.name, modifier.name, modifier.name)
                for modifier in bpy.context.view_layer.objects.active.modifiers]

    my_enum: EnumProperty(name="Modifier name",
                          items=item_list)

    # TODO add muilti modifier apply support
    # selection: BoolVectorProperty(
    #     size=32,
    #    options={'SKIP_SAVE'}
    # )

    # def draw(self, context):
    #    layout = self.layout
    #    for idx, mod in enumerate(context.active_object.modifiers):
    #        layout.prop(self, 'selection', index=idx, text=mod.name,
    #                    toggle=True)

    def execute(self, context):

        ob = context.view_layer.objects.active
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(True)
        context.view_layer.objects.active = ob

        # not great code ()
        area = bpy.context.area
        old_type = area.type
        area.type = 'VIEW_3D'

        apply_modifiers(context, self.my_enum)

        area.type = old_type

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()


# Menus #
def menu(self, context):
    if (context.active_object):
        if (len(context.active_object.modifiers)):
            layout = self.layout
            row = layout.row()
            row.operator(AWS_OT_operator.bl_idname,
                         icon='SHAPEKEY_DATA',
                         text="Apply Modifiers w/Shapekeys")


def menu_func(self, context):
    if (context.active_object):
        if (len(context.active_object.modifiers)):
            layout = self.layout
            layout.separator()
            layout.operator(AWS_OT_operator.bl_idname,
                            icon='SHAPEKEY_DATA',
                            text="Apply Modifiers w/Shapekeys")


def register():
    from bpy.utils import register_class

    register_class(AWS_OT_operator)

    # Add "Specials" menu to the "Modifiers" menu
    bpy.types.DATA_PT_modifiers.prepend(menu)

    # Add apply operator to the Apply 3D View Menu
    # bpy.types.VIEW3D_MT_object_apply.append(menu_func)


def unregister():
    # Remove "Specials" menu from the "Modifiers" menu.
    bpy.types.DATA_PT_modifiers.remove(menu)

    # Remove apply operator to the Apply 3D View Menu
    # bpy.types.VIEW3D_MT_object_apply.remove(menu_func)

    from bpy.utils import unregister_class
    unregister_class(AWS_OT_operator)


if __name__ == "__main__":
    register()
