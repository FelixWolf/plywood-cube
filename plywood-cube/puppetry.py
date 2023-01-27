import bpy
import uuid
import mathutils
import bl_math
import math
import bpy.props
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from mathutils import Vector
import llbase.llsd
import socket
import errno
import time
from . import sl_skeleton

Global = {}

PLYWOOD_CUBE_PUMP = uuid.UUID('acc4ce6d-f50d-417e-b7c6-cc5d6a6b850b')

class PuppetrySession:
    def __init__(self):
        self.props = None
        self.connected = False
        self.shouldClose = False
        self.pump = None
        self.buffer = b""
        self.length = None
        self.sock = None
        self.last = {}
        self.lastUpdate = 0
        bpy.app.timers.register(self.timer)
        bpy.app.timers.register(self.animate)
    
    def setProps(self, props):
        self.props = props
    
    def connect(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(1)
        self.sock.connect((host, port))
        self.sock.settimeout(0.1)
        self.connected = True
    
    def send(self, pump, data):
        if self.connected == False:
            return
        if not self.pump:
            return
        data = llbase.llsd.format_notation({"pump": pump, "data": data})
        data = str(len(data)).encode()+b":"+data
        print(data)
        return self.sock.sendall(data)
    
    def handleData(self, data):
        data = llbase.llsd.parse_notation(data)
        if not self.pump:
            self.pump = data
            #Disconnect any existing pumps
            self.send(self.pump["data"]["command"], {
                "op": "stoplisten",
                "reqid": -1,
                "source": "puppetry.controller",
                "listener": PLYWOOD_CUBE_PUMP
            })
            
            #Connect the pump
            self.send(self.pump["data"]["command"], {
                "op": "listen",
                "reqid": -1,
                "source": "puppetry.controller",
                "listener": PLYWOOD_CUBE_PUMP,
                "dest": "blender.plywood-cube.pupptry.controller"
            })
            
            self.send("puppetry", {
                "command": "set"
            })
        print(data)
        if data["pump"] == "puppetry.controller":
            pass
    
    def recv(self, size):
        self.sock.settimeout(0)
        return self.sock.recv(size)
    
    def animate(self):
        if self.shouldClose:
            return None
        if not self.connected:
            return 1
        if not self.props.Target:
            return 1
        if self.props.Target not in bpy.data.objects:
            return 1
        
        arm = bpy.data.objects[self.props.Target]
        
        updates = {}
        shouldUpdate = False
        for bn in arm.data.bones.keys():
            if bn not in self.props.Transmit:
                continue
            
            if not (self.props.Transmit[bn].position \
             or self.props.Transmit[bn].rotation):
                continue
            
            db = arm.data.bones[bn]
            pb = arm.pose.bones[bn]
            
            mat = pb.matrix_channel
            if pb.parent:
                mat = pb.parent.matrix_channel.inverted() @ mat
            
            r = mat.to_3x3().to_quaternion()
            
            r.normalize()
            
            if r.w < 0:
                r = r.inverted()
            
            loc, rot, scale = mat.decompose()
            
            if bn not in updates:
                updates[bn] = {}
            
            if self.props.Transmit[bn].rotation:
                updates[bn]["r"] = [
                    r.x,
                    r.y,
                    r.z,
                ]
            
            if self.props.Transmit[bn].position:
                updates[bn]["p"] = [
                    loc.x,
                    loc.y,
                    loc.z,
                ]
            
            if bn not in self.last:
                shouldUpdate = True
            else:
                for check in updates[bn].keys():
                    if check not in self.last[bn]:
                        shouldUpdate = True
                    elif self.last[bn][check] != updates[bn][check]:
                        shouldUpdate = True
                        
                for check in self.last[bn].keys():
                    if check not in updates[bn]:
                        shouldUpdate = True
        
        now = time.time()
        if shouldUpdate or now > self.lastUpdate + 0.5:
            self.last = updates
            self.lastUpdate = now
            self.send("puppetry", {
                "command": "set",
                "reply": None,
                "data": {
                    #Could also use "joint_state" instead of "j"
                    "j": updates
                }
            })
        return self.props.UpdateTime
    
    def timer(self):
        if self.shouldClose:
            return 0
        if not self.connected:
            return 1
        try:
            while self.connected:
                c = self.recv(1)
                if c == None or c == b"":
                    print("NO DATA")
                    self.disconnect()
                    break
                if self.length == None:
                    if c == b":":
                        self.length = int(self.buffer)
                        self.buffer = b""
                    else:
                        self.buffer += c
                    continue
                
                self.buffer += c
                if len(self.buffer) == self.length:
                    self.handleData(self.buffer)
                    self.buffer = b""
                    self.length = None
        except socket.error as e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                pass
            else:
                raise e
        return 0.01
    
    def disconnect(self):
        self.connected = False
        if self.sock:
            self.sock.close()
        self.sock = None
    
    def close(self):
        self.shouldClose = True
        self.disconnect()

#==============================================================================
# Blender Operator class
#==============================================================================
#Custom types
class PuppetryTransmitList(bpy.types.PropertyGroup):
    position: bpy.props.IntProperty(name="A")
    rotation: bpy.props.IntProperty(name="B")
    group: bpy.props.StringProperty()

class StringArrayProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()

#Connect submenu
class VIEW3D_OT_puppetry_connect(bpy.types.Operator):
    bl_idname = "puppetry.connect"
    bl_label = 'Connect to puppetry server'
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        Session = Global["Session"]
        layout = self.layout
        scene = context.scene
        props = scene.puppetry
        if Session.connected:
            Session.disconnect()
        else:
            Session.connect(props.Host, port=props.Port)
        return {'FINISHED'}


def add_items_from_collection_callback(self, context):
    return [(v.name, v.name, '') for v in bpy.context.scene.puppetry.TransmitGroups]

class PuppetryProperties(bpy.types.PropertyGroup):
    Host: bpy.props.StringProperty(
        name="Host",
        default="127.0.0.1",
        maxlen=1024,
    )

    Port: bpy.props.IntProperty(
        name="Port",
        default=5000,
        min=1024,
        max=65535
    )
    
    Armatures: bpy.props.CollectionProperty(type=StringArrayProperty)
    
    Target: bpy.props.StringProperty(name = "Target")
    
    Transmit: bpy.props.CollectionProperty(type=PuppetryTransmitList)
    Transmit_index: bpy.props.IntProperty()
    TransmitGroups: bpy.props.CollectionProperty(type=StringArrayProperty)
    TransmitGroupEnum: bpy.props.EnumProperty(items=add_items_from_collection_callback)
    
    UpdateTime: bpy.props.FloatProperty(
        name = "Update rate",
        default = 0.1,
        min = 0.05,
        max = 5
    )

class VIEW3D_PT_puppetry_connect(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Puppetry'
    bl_label = "Connection"
    
    def draw(self, context):
        Session = Global["Session"]
        layout = self.layout
        scene = context.scene
        props = scene.puppetry
        
        Session.setProps(props)

        layout.prop(props, "Host")
        layout.prop(props, "Port")
        layout.separator()
        if Session.connected:
            layout.operator('puppetry.connect', text = 'Disconnect')
        else:
            layout.operator('puppetry.connect', text = 'Connect')

#Armature submenu
@bpy.app.handlers.persistent
def findArmatures(self):
    findArmaturesReal()

def findArmaturesReal():
    context = bpy.context
    props = bpy.context.scene.puppetry

    props.Armatures.clear()
    
    for o in bpy.data.objects:
        if o.type == 'ARMATURE':
            armature = props.Armatures.add()
            armature.name = o.name
    
    if len(props.Armatures) == 1 and props.Target == "":
        props.Target = props.Armatures[0].name

class VIEW3D_OT_puppetry_skeleton_action(bpy.types.Operator):
    bl_idname = 'puppetry.skeletonedit'
    bl_label = ''
    
    action: bpy.props.IntProperty(
        name = 'action',
        default = -1
    )
    
    def execute(self, context):
        Session = Global["Session"]
        layout = self.layout
        scene = context.scene
        props = scene.puppetry
        if self.action == 0:
            if Session.connected:
                Session.send("puppetry", {
                    "command": "send_skeleton",
                    "reply": None
                })
        else:
            #Reset skeleton?
            pass
        return {'FINISHED'}

class VIEW3D_PT_puppetry_armature(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Puppetry'
    bl_label = "Armature"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.puppetry
        
        layout.prop_search(props, "Target", props, "Armatures", text="", icon="ARMATURE_DATA")
        layout.separator()
        layout.prop(props, "UpdateTime")
        row = layout.row()
        """
        row = layout.row(align=True)
        btn = row.operator("puppetry.skeletonedit", text="Sync Skeleton")
        btn.action = 0
        
        btn = row.operator("puppetry.skeletonedit", text="Reset Skeleton")
        btn.action = 1
        """
        

#Transmit submenu
class VIEW3D_OT_puppetry_transmit_toggle(bpy.types.Operator):
    bl_idname = 'puppetry.transmittoggle'
    bl_label = ''
    
    target: bpy.props.StringProperty(
        name = 'target'
    )
    
    property: bpy.props.StringProperty(
        name = 'property'
    )
    
    group: bpy.props.StringProperty(
        name = 'group'
    )
    
    value: bpy.props.IntProperty(
        name = 'value',
        default = -1
    )
    
    def match(self, prop):
        if not (self.target == "*" or prop.name == self.target):
            return False
        
        if self.group != "":
            if prop.group != self.group:
                return False
        
        return True
    
    def execute(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.puppetry
        for p in props.Transmit:
            if self.match(p):
                if self.value == -1:
                    setattr(p, self.property, not getattr(p, self.property))
                else:
                    setattr(p, self.property, bool(self.value))
        return {'FINISHED'}

class VIEW3D_UL_puppetry_transmit(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.row()
            split.label(text=item.name)
            
            split2 = layout.row()
            split2.alignment = "RIGHT"
            
            btn = split2.operator("puppetry.transmittoggle", icon="OBJECT_ORIGIN" if item.position else "DOT", emboss = False)
            btn.target = item.name
            btn.property = "position"
            btn = split2.operator("puppetry.transmittoggle", icon="ORIENTATION_GIMBAL" if item.rotation else "DOT", emboss = False)
            btn.target = item.name
            btn.property = "rotation"
            
    
    def draw_filter(self, context, layout):
        scene = context.scene
        props = scene.puppetry
        row = layout.row()
        row.prop(props, "TransmitGroupEnum", text = "")
    
    def filter_items(self, context, data, propname):
        filtered = []
        ordered = []
        items = getattr(data, propname)
        for item in items:
            if item.group == bpy.context.scene.puppetry.TransmitGroupEnum:
                filtered.append(self.bitflag_filter_item)
            else:
                filtered.append(~self.bitflag_filter_item)
        return filtered, ordered

class VIEW3D_PT_puppetry_transmit(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Puppetry'
    bl_label = "Transmit List"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.puppetry

        row = layout.row()
        row.template_list(
            "VIEW3D_UL_puppetry_transmit", "custom_def_list",
            props, "Transmit",
            props, "Transmit_index",
            rows=2
        )
        
        row = layout.row()
        row.label(text="Enable:", icon="OBJECT_ORIGIN")
        
        row = layout.row(align=True)
        btn = row.operator("puppetry.transmittoggle", text="All")
        btn.target = "*"
        btn.property = "position"
        btn.value = 1
        
        btn = row.operator("puppetry.transmittoggle", text="Group")
        btn.target = "*"
        btn.property = "position"
        btn.group = props.TransmitGroupEnum
        btn.value = 1
        
        btn = row.operator("puppetry.transmittoggle", text="Selected")
        
        
        row = layout.row()
        row.label(text="Disable:", icon="OBJECT_ORIGIN")
        
        row = layout.row(align=True)
        btn = row.operator("puppetry.transmittoggle", text="All")
        btn.target = "*"
        btn.property = "position"
        btn.value = 0
        
        btn = row.operator("puppetry.transmittoggle", text="Group")
        btn.target = "*"
        btn.property = "position"
        btn.group = props.TransmitGroupEnum
        btn.value = 0
        
        btn = row.operator("puppetry.transmittoggle", text="Selected")
        
        
        row = layout.row()
        row.label(text="Enable:", icon="ORIENTATION_GIMBAL")
        
        row = layout.row(align=True)
        btn = row.operator("puppetry.transmittoggle", text="All")
        btn.target = "*"
        btn.property = "rotation"
        btn.value = 1
        
        btn = row.operator("puppetry.transmittoggle", text="Group")
        btn.target = "*"
        btn.property = "rotation"
        btn.group = props.TransmitGroupEnum
        btn.value = 1
        
        btn = row.operator("puppetry.transmittoggle", text="Selected")
        
        row = layout.row()
        row.label(text="Disable:", icon="ORIENTATION_GIMBAL")
        row = layout.row(align=True)
        btn = row.operator("puppetry.transmittoggle", text="All")
        btn.target = "*"
        btn.property = "rotation"
        btn.value = 0
        
        btn = row.operator("puppetry.transmittoggle", text="Group")
        btn.target = "*"
        btn.property = "rotation"
        btn.group = props.TransmitGroupEnum
        btn.value = 0
        
        btn = row.operator("puppetry.transmittoggle", text="Selected")

def populateBoneList():
    transmit = bpy.context.scene.puppetry.Transmit
    groups = bpy.context.scene.puppetry.TransmitGroups
    transmit.clear()
    groups.clear()
    
    bones = sl_skeleton.get_skeleton()
    addedGroups = []
    for bone in bones:
        if bone["group"] not in addedGroups:
            addedGroups.append(bone["group"])
            g = groups.add()
            g.name = bone["group"].capitalize()
        b = transmit.add()
        b.name = bone["name"]
        b.group = bone["group"]

#Registration

module_classes = (
    VIEW3D_OT_puppetry_transmit_toggle,
    StringArrayProperty,
    PuppetryTransmitList,
    PuppetryProperties,
    VIEW3D_OT_puppetry_skeleton_action,
    VIEW3D_OT_puppetry_connect,
    VIEW3D_PT_puppetry_connect,
    VIEW3D_PT_puppetry_armature,
    VIEW3D_UL_puppetry_transmit,
    VIEW3D_PT_puppetry_transmit
)

def register():
    for cls in module_classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.puppetry = bpy.props.PointerProperty(type=PuppetryProperties)
    
    Global["Session"] = PuppetrySession()
    bpy.app.handlers.depsgraph_update_post.append(findArmatures)
    bpy.app.timers.register(lambda: findArmaturesReal() or 1)
    bpy.app.timers.register(lambda: populateBoneList() or None)


def unregister():
    Session = Global["Session"]
    
    del bpy.types.Scene.puppetry
    bpy.app.handlers.depsgraph_update_post.remove(findArmatures)
    
    for cls in reversed(module_classes):
        bpy.utils.unregister_class(cls)
    
    Session.close()
    del Global["Session"]
    