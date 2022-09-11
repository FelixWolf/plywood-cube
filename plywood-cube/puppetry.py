import bpy
import uuid
import mathutils
import bl_math
import math
from bpy.types import Operator, PropertyGroup
from bpy.props import FloatVectorProperty, StringProperty, IntProperty, PointerProperty, CollectionProperty, FloatProperty
import bpy.props
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from mathutils import Vector
import llbase.llsd
import socket
import errno
import time

Global = {}

class PuppetrySession:
    def __init__(self):
        self.props = None
        self.connected = False
        self.shouldClose = False
        self.pump = None
        self.buffer = b""
        self.length = None
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
    
    def send(self, data):
        if self.connected == False:
            return
        if not self.pump:
            return
        data = llbase.llsd.format_notation({"pump": "puppetry", "data": data})
        data = str(len(data)).encode()+b":"+data
        return self.sock.sendall(data)
    
    def handleData(self, data):
        data = llbase.llsd.parse_notation(data)
        if not self.pump:
            self.pump = data
    
    def recv(self, size):
        self.sock.settimeout(0)
        return self.sock.recv(size)
    
    def animate(self):
        if self.shouldClose:
            return 0
        if not self.connected:
            return 1
        if not self.props.Target:
            return 1
        if self.props.Target not in bpy.data.objects:
            return 1
        arm = bpy.data.objects[self.props.Target]
        if getattr(arm.animation_data, "action", None) == None:
            return 1
        
        updates = {}
        shouldUpdate = False
        for fcurve in arm.animation_data.action.fcurves:
            if fcurve.group.name not in arm.pose.bones:
                continue
            
            l = arm.data.bones[fcurve.group.name].matrix_local.to_quaternion()
            r = arm.pose.bones[fcurve.group.name].matrix_basis.to_quaternion()
            
            parent = arm.pose.bones[fcurve.group.name].parent
            
            r = r
            if r.w < 0:
                r = r.inverted()
            
            r.normalize()
            
            
            if fcurve.group.name not in updates:
                updates[fcurve.group.name] = {}
            
            updates[fcurve.group.name]["local_rot"] = [
                r.x,
                r.y,
                r.z,
            ]
            
            if fcurve.group.name not in self.last:
                shouldUpdate = True
            else:
                for check in updates[fcurve.group.name].keys():
                    if check not in self.last[fcurve.group.name]:
                        shouldUpdate = True
                    elif self.last[fcurve.group.name][check] != updates[fcurve.group.name][check]:
                        shouldUpdate = True
        
        now = time.time()
        if shouldUpdate or now > self.lastUpdate + 0.5:
            self.last = updates
            self.lastUpdate = now
            self.send({
                "command": "move",
                "reply": None,
                **updates
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

class StringArrayProperty(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty()

class PuppetryProperties(PropertyGroup):
    Host: StringProperty(
        name="Host",
        default="127.0.0.1",
        maxlen=1024,
    )

    Port: IntProperty(
        name="Port",
        default=5000,
        min=1024,
        max=65535
    )
    
    Armatures: CollectionProperty(type=StringArrayProperty)
    Target: StringProperty(name = "Target")
    UpdateTime: FloatProperty(
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

@bpy.app.handlers.persistent
def findArmatures(self):
    context = bpy.context
    props = bpy.context.scene.puppetry

    props.Armatures.clear()
    
    for o in bpy.data.objects:
        if o.type == 'ARMATURE':
            armature = props.Armatures.add()
            armature.name = o.name
    
    if len(props.Armatures) == 1 and props.Target == "":
        props.Target = props.Armatures[0].name

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
        

def factory_update_addon_category(cls, prop):
    def func(self, context):
        if hasattr(bpy.types, cls.__name__):
            bpy.utils.unregister_class(cls)
        cls.bl_category = self[prop]
        bpy.utils.register_class(cls)
    return func

class PuppetryAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    connect_category: bpy.props.StringProperty(
        name="Connection", description="Category in 3D View Toolbox where the connection panel is displayed",
        default="Puppetry", update=factory_update_addon_category(VIEW3D_PT_puppetry_connect, 'connect_category'))

    def draw(self, context):
        sub = self.layout.column(align=True)
        sub.use_property_split = True
        sub.label(text="3D View Panel Category:")
        sub.prop(self, "connect_category", text="Connect Panel:")


module_classes = (
    StringArrayProperty,
    PuppetryProperties,
    VIEW3D_OT_puppetry_connect,
    VIEW3D_PT_puppetry_connect,
    VIEW3D_PT_puppetry_armature,
    PuppetryAddonPreferences,
)

def register():
    for cls in module_classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.puppetry = PointerProperty(type=PuppetryProperties)
    
    Global["Session"] = PuppetrySession()
    bpy.app.handlers.depsgraph_update_post.append(findArmatures)


def unregister():
    Session = Global["Session"]
    
    del bpy.types.Scene.puppetry
    bpy.app.handlers.depsgraph_update_post.remove(findArmatures)
    
    for cls in reversed(module_classes):
        bpy.utils.unregister_class(cls)
    
    Session.close()
    del Global["Session"]
    