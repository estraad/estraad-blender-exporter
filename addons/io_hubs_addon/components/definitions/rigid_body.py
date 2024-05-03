from bpy.props import BoolProperty, FloatProperty, EnumProperty, BoolVectorProperty, FloatVectorProperty
from ..hubs_component import HubsComponent
from ..types import NodeType, PanelType, Category
from mathutils import Vector


collision_masks = [
    ("objects", "Objects", "Interactive objects"),
    ("triggers", "Triggers", "Trigger Colliders"),
    ("environment", "Environment", "Environment geometry"),
    ("avatars", "Avatars", "Player Avatars"),
    ("media-frames", "Media Frames", "Media Frames"),
]


class RigidBody(HubsComponent):
    _definition = {
        'name': 'rigidbody',
        'display_name': 'RigidBody',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'PHYSICS',
        'deps': ['physics-shape'],
        'version': (1, 0, 1)
    }

    type: EnumProperty(
        name="Body Type",
        description="RigidBody Type",
        items=[("static", "Static", "Will not ever move."),
               ("dynamic", "Dynamic", "Effected by physics and gravity"),
               ("kinematic", "Kinematic", "Not effected by gravity or collisions, but can be moved.")],
        default="dynamic")

    disableCollision: BoolProperty(
        name="Is Trigger",
        description="Disable collision response, act as a trigger only",
        default=False)

    collisionGroup: EnumProperty(
        name="Collision Group",
        description="What collision group this object belongs to. This effects what objects will collide with it.",
        items=[g for g in collision_masks if g[0] != "avatars"],
        default="objects")

    collisionMask: BoolVectorProperty(
        name="Collision Mask",
        description="What collision groups this object will collide with. Note: the other object must also be set to collide with this object's group.",
        size=5, subtype='LAYER', options={'ANIMATABLE'},
        default=[value in ["objects", "triggers", "environment"] for (value, _label, _desc) in collision_masks])

    mass: FloatProperty(
        name="Mass",
        description="Object's Mass",
        default=1)

    linearDamping: FloatProperty(
        name="Linear Damping",
        description="Amount of linear damping",
        default=0,
        min=0.0,
        soft_max=1.0,
    )

    angularDamping: FloatProperty(
        name="Angular Damping",
        description="Amount of angular damping",
        default=0,
        min=0.0,
        soft_max=1.0,
    )

    linearSleepingThreshold: FloatProperty(
        name="Linear Sleeping Threshold",
        description="Linear velocity threshold below which the object starts to sleep",
        default=0.8,
        min=0.0,
        soft_max=10.0,
    )

    angularSleepingThreshold: FloatProperty(
        name="Angular Sleeping Threshold",
        description="Angular velocity threshold below which the object starts to sleep",
        default=1.0,
        min=0.0,
        soft_max=10.0,
    )

    angularFactor: FloatVectorProperty(
        name="Angular Factor",
        description="Influence of the object's rotation along the X, Y, and Z axes",
        size=3,
        subtype="XYZ",
        default=(1.0, 1.0, 1.0),
        min=0.0,
        soft_max=10.0,
    )

    gravity: FloatVectorProperty(
        name="Gravity", description="Object's Gravity",
        unit="ACCELERATION",
        subtype="ACCELERATION",
        default=(0.0, -9.8, 0.0))

    def gather(self, export_settings, object):
        props = super().gather(export_settings, object)
        props['collisionMask'] = [value for i, (value, _label, _desc) in enumerate(
            collision_masks) if self.collisionMask[i]]
        # prefer to store as an array for new components
        props['gravity'] = [v for v in self.gravity]
        props['angularFactor'] = [v for v in self.angularFactor]
        return props

    def draw(self, context, layout, panel):
        layout.prop(self, "type")

        if (self.disableCollision and self.collisionGroup != "triggers") or (self.collisionGroup == "triggers" and not self.disableCollision):
            col = layout.column()
            # col.alert = True
            col.label(
                text="When making triggers you likely want 'Is Trigger' checked and collision group set to 'Triggers'",
                icon='INFO')
        layout.prop(self, "collisionGroup")
        layout.label(text="Collision Mask:")
        col = layout.column(align=True)
        for i, (_value, label, _desc) in enumerate(collision_masks):
            col.prop(self, "collisionMask", text=label, index=i, toggle=True)
        layout.prop(self, "disableCollision")

        layout.prop(self, "mass")
        layout.prop(self, "linearDamping")
        layout.prop(self, "angularDamping")
        layout.prop(self, "linearSleepingThreshold")
        layout.prop(self, "angularSleepingThreshold")
        layout.prop(self, "angularFactor")
        layout.prop(self, "gravity")

    @classmethod
    def init(cls, obj):
        obj.hubs_component_list.items.get('physics-shape').isDependency = True

    def gather(self, export_settings, object):
        props = super().gather(export_settings, object)
        props['angularFactor'] = {
            'x': self.angularFactor[0],
            'y': self.angularFactor[2] if export_settings['gltf_yup'] else self.angularFactor[1],
            'z': self.angularFactor[1] if export_settings['gltf_yup'] else self.angularFactor[2],
        }
        props['gravity'] = {
            'x': self.gravity[0],
            'y': self.gravity[2] if export_settings['gltf_yup'] else self.gravity[1],
            'z': self.gravity[1] if export_settings['gltf_yup'] else self.gravity[2],
        }
        return props

    def migrate(self, migration_type, panel_type, instance_version, host, migration_report, ob=None):
        migration_occurred = False
        if instance_version <= (1, 0, 0):
            migration_occurred = True

            angularFactor = self.angularFactor.copy()
            angularFactor = Vector((angularFactor.x, angularFactor.z, angularFactor.y))
            self.angularFactor = angularFactor

            gravity = self.gravity.copy()
            gravity = Vector((gravity.x, gravity.z, gravity.y))
            self.gravity = gravity

        return migration_occurred
