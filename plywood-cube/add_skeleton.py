import bpy
import mathutils
import bl_math
import math
import os
from bpy.types import Operator, PropertyGroup
from bpy.props import FloatVectorProperty, StringProperty, IntProperty, PointerProperty, CollectionProperty, FloatProperty
import bpy.props
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from mathutils import Vector
import xml.etree.ElementTree as ET

def add_skeleton(self, context):
    tree = ET.parse(os.path.join(os.path.dirname(os.path.realpath(__file__)), "character/avatar_skeleton.xml"))
    root = tree.getroot()
    def getRecursive(bone, parent=None):
        result = []
        entry = {
            "name": bone.attrib["name"],
            "pos_orig": [float(i) for i in bone.attrib["pos"].split(" ")],
            "end_orig": [float(i) for i in bone.attrib["end"].split(" ")],
            "rot_orig": [float(i) for i in bone.attrib["rot"].split(" ")],
            "scale_orig": [float(i) for i in bone.attrib["scale"].split(" ")],
            "parent": parent["name"] if parent else False,
            "connected": bone.attrib.get("connected", "false").lower() == "true",
            "group": bone.tag
        }
        
        if parent:
            offset = parent["pos"]
            entry["pos"] = [entry["pos_orig"][i]+offset[i] for i in range(0,3)]
        else:
            entry["pos"] = entry["pos_orig"]
        entry["end"] = [entry["end_orig"][i]+entry["pos"][i] for i in range(0,3)]
        
        entry["scale"] = mathutils.Matrix.Scale(entry["scale_orig"][0], 4, (1,0,0))
        entry["scale"] *= mathutils.Matrix.Scale(entry["scale_orig"][1], 4, (0,1,0))
        entry["scale"] *= mathutils.Matrix.Scale(entry["scale_orig"][2], 4, (0,0,1))
        
        entry["rot"] = mathutils.Euler(entry["rot_orig"], "XYZ").to_matrix().to_4x4()
        
        result.append(entry)
        
        for child in bone:
            result += getRecursive(child, parent=entry)
        return result
    
    bones = getRecursive(root[0])
    
    armature = bpy.data.armatures.new(name="Armature")
    armature_obj = bpy.data.objects.new("Armature", armature)
    context.collection.objects.link(armature_obj)
    armature_obj.select_set(True)
    context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    edit_bones = armature.edit_bones
    pose = armature_obj.pose
    boners = {}
    for bone in bones:
        b = edit_bones.new(bone["name"])
        boners[bone["name"]] = b
        b.head = bone["pos"]
        b.tail = bone["end"]
        if bone["parent"]:
            b.parent = boners[bone["parent"]]
        
        if bone["connected"]:
            b.use_connect = True
    #Remove auto-created bone
    bpy.ops.object.mode_set(mode='EDIT',toggle=True)
    pose.bone_groups.new(name="bone")
    pose.bone_groups.new(name="collision_volume")
    pose.bone_groups["collision_volume"].color_set = "THEME01"
    bone_matrix = {}
    for bone in bones:
        pose.bones[bone["name"]].bone_group = pose.bone_groups[bone["group"]]
        bone_matrix[bone["name"]] = armature.bones[bone["name"]].matrix_local
    
    armature_obj.location = (0,0,0)
    return armature_obj, bone_matrix

#==============================================================================
# Blender Operator class
#==============================================================================
def add_skeleton_button(self, context):
    self.layout.operator(
        OBJECT_OT_add_skeleton.bl_idname,
        text="Add Second Life Skeleton",
        icon="ARMATURE_DATA")

class OBJECT_OT_add_skeleton(Operator, AddObjectHelper):
    """Create a new Mesh Object"""
    bl_idname = "add.sl_skeleton"
    bl_label = "Add Second Life Skeleton"
    bl_options = {'REGISTER', 'UNDO'}

    scale: FloatVectorProperty(
        name="scale",
        default=(1.0, 1.0, 1.0),
        subtype='TRANSLATION',
        description="scaling",
    )

    def execute(self, context):
        add_skeleton(self, context)
        return {'FINISHED'}

module_classes = (
    OBJECT_OT_add_skeleton,
)

def register():
    for cls in module_classes:
        bpy.utils.register_class(cls)
    #bpy.utils.register_manual_map(add_skeleton_manual_map)
    bpy.types.VIEW3D_MT_add.append(add_skeleton_button)


def unregister():
    for cls in reversed(module_classes):
        bpy.utils.unregister_class(cls)
    #bpy.utils.unregister_manual_map(add_skeleton_manual_map)
    bpy.types.VIEW3D_MT_add.remove(add_skeleton_button)

