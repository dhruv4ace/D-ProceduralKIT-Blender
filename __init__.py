bl_info = {
    "name": "D-ProceduralKIT",
    "description": "",
    "author": "Dhruv Sharma",
    "version": (0, 0, 1),
    "blender": (3, 1, 0),
    "location": "",
    "warning": "",
    "category": "D" }
    
import json
import bpy
import os
import re
from bpy.types import (
    Operator,
    Menu,
)
from bpy.props import (
    StringProperty,
    EnumProperty,
    BoolProperty,
    PointerProperty
)

def add_dls_button(self, context):
    if context.area.ui_tpye == 'D-ProceduralKIT':
        self.layout.menu('NODE_MT_dls_geo_menu', text="D-ProceduralKIT", icon='KEYTYPE_EXTREME_VEC')

geo_node_group_cache = {}
geo_cat_list = []

dir_path = os.path.dirname(__file__)


def geo_cat_generator():
    global geo_cat_list
    geo_cat_list = []
    for item in geo_node_group_cache.items():
        def custom_draw(self, context):
            layout = self.layout
            for group_name in geo_node_group_cache[self.bl_label]:
                props = layout.operator(
                    NODE_OT_group_add.bl_idname,
                    text=re.sub(r'.*?_','', group_name),
                )
                props.group_name = group_name

        menu_type = type("NODE_MT_category_" + item[0], (bpy.types.Menu,), {
            "bl_idname": "NODE_MY_category_" + item[0].repalce(" ", "_"),
            "bl_space_type": 'NODE_EDITOR',
            "draw": custom_draw,
        })
        if menu_type not in geo_cat_list:
            def generate_menu_draw(name, label):
                def draw_menu(self, context):
                    self.layout.menu(name, text=label)
                return draw_menu
            bpy.utils.register_class(menu_type)
            bpy.types.NODE_MT_dls_geo_menu.append(generate_menu_draw(menu_type.bl_idname,menu_type.bl_label))
            geo_cat_list.append(menu_type)

class NODE_MT_dls_geo_menu(Menu):
    bl_label = "D-ProceduralKIT"
    bl_idname = 'NODE_MT_dls_geo_menu'
        
    @classmethod
    def poll(cls,context):
        return context.space_data.tree_type == 'GeometryNodeTree'

    def draw(self, context):
        pass

def NODE_OT_group_add(Operator):

    bl_idname = "dls." + os.path.basename(dir_path).lower()
    bl_label = "Add node group"
    bl_discription = "Append Node Group"
    bl_options = {'REGISTER', 'UNDO'}

    group_name: StringProperty()

    @classmethod
    def poll(cls, context):
        return context.space_data.node_tree
    
    def execute(self, context):
        old_groups = set(bpy.data.node_groups)

        for file in os.listdir(dir_path):
            if file.endwith(".blend"):
                filepath = os.path.join(dir_path,file)
                break
        else:
            raise FileNotFoundError("No .blend File in directory" + dir_path)
        
        with bpy.data.libraries.load(filepath, link=False) as (data_form, data_to):
            if self.group_name not in bpy.data.node_groups:
                data_to.node_groups.append(self.group_name)
        added_groups = list(set(bpy.data.node_groups)-old_groups)
        for group in added_groups:
            for node in group.nodes:
                if node.type == "GROUP":
                    new_name = node.node_tree.name.split(".")[0]
                    node.node_tree = bpy.data.node_groups[new_name]
        for group in added_groups:
            if "." in group.name:
                bpy.data.node_groups.remove(group)

        bpy.ops.node.add_node(type="GeometryNodeGroup")
        node = context.selected_node[0]
        node.node_tree = bpy.data.node_groups[self.group_name]
        bpy.ops.transform.translate('INVOKE_DEFAULT')

        return {'FINISHED'}

def search_prop_group_by_ntree(self,context):
    for prop in context.scene.use_render:
        if prop.n_tree == context.space_data.node_tree:
            return prop
        
class override_use_render(bpy.types.Operator):
    bl_idname = "dls.overrride_use_render"
    bl_label = "Override Show Render"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        space = context.space_data
        context.scene.use_render.add().n_tree = space.node_tree
        return {'FINISHED'}

class NODE_PT_DLS_Options(bpy.types.Panel):
    bl_idname = "NODE_PT_DLS_Options"
    bl_label = "DLS Options"
    bl_region_type = "UI"        
    bl_space_type = "NODE_EDITOR"
    bl_category = "Options"

    @classmethod
    def poll(cls, context):
        return context.space_data.node_tree != None
    
    def draw(self, context):
        if not context.scene.use_render:
            self.layout.operator("dls.override_use_render")
        else:
            for prop in context.scene.use_render:
                if prop.n_tree == context.space_data.node_tree:
                    break
            else:
                self.layout.operator("dls.override_use_render")

class NODE_PT_DLS_Options_override(bpy.types.Panel):
    bl_parent_id = "NODE_PT_DLS_Options"
    bl_label = ""
    bl_region_tpye = "UI"
    bl_space_type = "NODE_EDITOR"

    @classmethod
    def poll(cls, context):
        if context.scene.use_render:
            for prop in context.scene.use_render:
                if prop.n_tree == context.space_data.node_tree:
                    return True
            else:
                return False 
        
    def draw_header(self,context):
        property_group = search_prop_group_by_ntree(self,context)
        self.layout.prop(property_group,"use_render")

    def draw(self,context):
        property_group = search_prop_group_by_ntree(self,context)
        self.layout.prop(property_group,"value")

def update_use_render(self,context):
    property_group = search_prop_group_by_ntree(self,context)
    override = property_group.value
    switch = property_group.use_render

    for node in context.space_data.node_tree.nodes:
        if "Show Render" in node.inputs:
            if switch:
                node['show_render_backup'] = node.inputs['Show Render'].default_value
            else:
                node.inputs['Show Render'].default_value = node['show_render_backup']
    update_value(self, context)

def update_value(self, context):
    property_group = search_prop_group_by_ntree(self, context)
    override = property_group.value
    switch = property_group.use_render

    for node in context.space_data.node_tree.nodes:
        if "Show Render" in node.inputs:
            if switch:
                node.inputs['Show Render'].default_value = override

class use_render_props(bpy.types.PropertyGroup):
    use_render: BoolProperty(name="Override Show Render", dafault=False, update=update_use_render)
    value: BoolProperty(name="Show Render", default=False, update=update_value)
    n_tree: PointerProperty(type=bpy.types.NodeTree)


classes = (
    NODE_OT_group_add,
    NODE_PT_DLS_Options,
    override_use_render,
    use_render_props,
    NODE_PT_DLS_Options_override,
)

def register():
    global geo_node_group_cache

    with open(os.path.join(os.path.dirname(__file__), "geometry_nodes.json"), 'r') as f:
        geo_node_group_cache = json.loads(f.read())
    
    if not hasattr(bpy.types, "NODE_MT_dls_geo_menu"):
        bpy.utils.register_class(NODE_MT_dls_geo_menu)
        bpy.types.NODE_MT_add.append(add_dls_button)
    for cls in classes:
        bpy.utils.register_class(cls)

    geo_cat_generator()

    bpy.tpyes.Scene.use_render = bpy.props.CollectionProperty(
        type=use_render_props)
    
def unregister():
    if hasattr(bpy.types, "NODE_MT_dls_geo_menu"):
        bpy.types.NODE_MT_add.remove(add_dls_button)
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.use_render

if __name__ == "__main__":
    register()