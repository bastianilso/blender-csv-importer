bl_info = {  
 "name": "Import Statistical Data (*.csv)",  
 "author": "Bastian Ilso (bastianilso)",  
 "version": (0, 2),  
 "blender": (2, 7, 8),  
 "location": "File > Import > Import Statistical Data (*.csv)",  
 "description": "Import, visualize and animate data stored as *.csv",  
 "warning": "",
 "wiki_url": "",  
 "tracker_url": "https://github.com/bastianilso/blender-csv-importer",  
 "category": "Import-Export"}

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, PointerProperty, FloatVectorProperty
from bpy.types import Operator, PropertyGroup
import csv
import bmesh
import random
from math import radians, degrees
from mathutils import Vector, Color
from collections import Counter


class Utils():

    # http://stackoverflow.com/questions/354038/how-do-i-check-if-a-string-is-a-number-float-in-python    
    def is_number(self, v):
        try:
            float(v)
        except ValueError:
            return False
        else:
            return True
    
    # get approximate dimensions of the visual area which the objects cover
    def measure_bl_array_dimensions(self, objects):
        dimensions = None
        max_x = 0
        max_y = 0
        max_z = 0
        for i in range(len(objects)-1):
            if (objects[i].location.x > max_x):
                max_x = objects[i].location.x
            if (objects[i].location.y > max_y):
                max_y = objects[i].location.y
            if (objects[i].location.z > max_z):
                max_z = ob.location.z

        return (max_x, max_y, max_z)
    
    # normalizes scale whilst maintaining aspect ratio
    def normalize_objects(self, objects, scale):
        dimensions = self.measure_bl_array_dimensions(objects)
        max_number = max(dimensions)
        scale_number = scale / max_number
        for (i,ob) in enumerate(objects):
            ob.scale = (ob.scale.x * scale_number, ob.scale.y * scale_number, ob.scale.z * scale_number)
            ob.location = (ob.location.x * scale_number, ob.location.y * scale_number, ob.location.z * scale_number)

    # Based on:
    # https://gifguide2code.wordpress.com/2017/04/09/python-how-to-code-materials-in-blender-cycles/
    def create_shadeless_cycles_mat(self,color=(0.08,0.09,0.1),id=''):
        # initialize node
        mat_name = "VisualizationMat" + id
        mat = bpy.data.materials.new(mat_name)
        bpy.data.materials[mat_name].use_nodes = True
        
        # connect emission node with material output node
        bpy.data.materials[mat_name].node_tree.nodes.new(type='ShaderNodeEmission')
        inp = bpy.data.materials[mat_name].node_tree.nodes['Material Output'].inputs['Surface']
        outp = bpy.data.materials[mat_name].node_tree.nodes['Emission'].outputs['Emission']
        bpy.data.materials[mat_name].node_tree.links.new(inp,outp)

        # connect light path node to emission node
        bpy.data.materials[mat_name].node_tree.nodes.new(type='ShaderNodeLightPath')
        inp = bpy.data.materials[mat_name].node_tree.nodes['Emission'].inputs['Strength']
        outp = bpy.data.materials[mat_name].node_tree.nodes['Light Path'].outputs['Is Camera Ray']
        bpy.data.materials[mat_name].node_tree.links.new(inp,outp)

        # Change emission color
        bpy.data.materials[mat_name].node_tree.nodes['Emission'].inputs['Color'].default_value = (color[0],color[1],color[2],1.0)
        bpy.data.materials[mat_name].diffuse_color = color
        bpy.data.materials[mat_name].use_shadeless = True
        
        return bpy.data.materials[mat_name]

    # Create a number of colors with similar, hue, saturation and value as a target color.
    def create_adjacent_colors(self, primary_color, amount):
        colors = []
        influence_pool = 0.3
        influencers = [0.1,0.1]        
        satval = [0.0, 0.0]
        if (primary_color.s > 0.8):
            influencers[0] = influencers[0] * (-1)
        if (primary_color.s < 0.01):
            influencers[0] = 0.0 # assume greyscale
            influencers[1] = 0.6

        if (primary_color.v > 0.8):
            influencers[1] = influencers[1] * (-1)
        if (primary_color.v < 0.1):
            influencers[1] = influencers[1] + 0.2

        flipper = 1
        for x in range(amount):
            color = primary_color.copy()
            color.h = color.h + random.uniform(0.00,0.05) * flipper # select hue at random
            while (influence_pool > 0):
                satval[0] += random.uniform(0.00,influencers[0])
                influence_pool -= abs(satval[0])
                if (influence_pool > 0):
                    satval[1] += random.uniform(0.00,influencers[1])
                    influence_pool -= abs(satval[1])
            random.shuffle(satval)
            color.s = color.s + satval[0]
            color.v = color.v + satval[1]
            colors.append(color)
            color = []
            satval = [0.0, 0.0]
            influence_pool = 0.5
            flipper = flipper * (-1)
        
        return colors
    

# DataStorage is essentially a class around a two-dimensional array with 
# functions to store dataset headers, extract frequencies etc.
class DataStorage():
    
    data = None
    data_numeric = None
    headers = None

    def __init__(self, d = None):
        self.data = d
    
    def add_row(self, row):        
        # TODO: zero-pad all entries if the length of a row exceeds already added rows.
        # Use the length of the first row to determine amount of columns
        if (self.data == None):
            self.data = []
            self.data = [[] for i in range(len(row))]
        utils = Utils()

        # Append values from each parsed row into the array.
        for (j,v) in enumerate(row):
            if (utils.is_number(v)):
                self.data[j].append(float(v))
            else:
                self.data[j].append(v)
    
    def get_columns(self, type=''):
        utils = Utils()
        data = self.data

        # AS_NUMERIC converts string data to numeric representations
        if (type == 'AS_NUMERIC'):
            # Loop through each column
            for i in range(len(data)):
                # Check if the first value is a number, skip if true.
                if (utils.is_number(data[i][0])):
                    continue
                else:
                    # Learn what categories are here
                    cate_count, categories = self.get_string_frequencies(i)
                    # Run through each string value
                    # Use the index of the category name as numerical representation
                    for j in range(len(data[i])):
                        data[i][j] = categories.index(data[i][j])                        
        return data

    def get_string_frequencies(self, column):
        data = self.data
        categories = []
        cate_count = []
        
        cnt = Counter()
        for word in data[column]:
            cnt[word] += 1
        
        categories = list(cnt.keys())
        cate_count = list(cnt.values())
            
        return (cate_count, categories)     
            
    def get_numeric_frequencies(self, column, split):
        data = self.data
        max_value = max(data[column])
        min_value = min(data[column])
        data_range = max_value - min_value
        divide = data_range / split
        categories = []
        cate_count = []

        for i in range(0, split):            
            # Calculate lowest value and highest value for each category
            # Rounding to 2 decimals fixes some gaps (but not all..)
            lv = min_value + (divide * i)
            hv = min_value + (divide * (i+1))

            # Create category name
            categories.append(str('{0:.2f}'.format(lv)) + ' - ' + str('{0:.2f}'.format(hv)))      
            
            # initialize cate_counts
            cate_count.append(0)
            
            # Find numbers which fit in category.
            for j in range(len(data[column])):
                v = data[column][j]
                if (v <= hv and v >= lv):
                    cate_count[i] += 1
                                
        return (cate_count, categories)

    def get_frequencies(self, column, output_type='', split=None):
        utils = Utils()
        data = self.data
        cate_count = []
        categories = []
        
        if (utils.is_number(data[column][0])):
            cate_count, categories = self.get_numeric_frequencies(column, split)
        else:
            cate_count, categories = self.get_string_frequencies(column)

        total = sum(c for c in cate_count)
        
        if (output_type == 'DEGREES'):
            multiplier = 360
        elif (output_type == 'PERCENTAGE'):
            multiplier = 100
        else: # return as decimal values
            multiplier = 1
        
        for i in range(len(cate_count)):
            cate_count[i] = float(cate_count[i]) / float(total)
            cate_count[i] = round(cate_count[i] * multiplier,2)
        
        return (cate_count, categories)

# ObjectVisualizer is a Visualizer which instantiates objects
# based on frequency in a target data column.
class ObjectVisualizer():

    dataStore = None
    bl_objects = []
    props = None
    user_object = None
    material = None
    
    def visualize(self, dataStorage):
        self.dataStore = dataStorage
        self.props = bpy.context.scene.import_csv.visprops
        self.bl_objects = self.create_blender_objects()
        if (self.props.use_animate):
            self.animate_objects()

    def create_blender_objects(self):
        headers = self.dataStore.headers
        objects = []
        split = self.props.split
        data = self.dataStore.get_columns()
        column = min(self.props.column, len(data)) -1
        area = 1.0
        cate_count, categories = self.dataStore.get_frequencies(column,'PERCENTAGE',split)
        objects = []
        width = 5
        utils = Utils()
        
        if self.props.point_object:
            user_object = bpy.data.objects[self.props.point_object]
            individual_offset = (user_object.dimensions.x / 3)
            offset = (user_object.dimensions.x / 2)
            self.material = user_object.active_material
        else:
            bpy.ops.object.add(radius=0.1)
            user_object = bpy.context.object
            individual_offset = 0.3
            offset = 0.5
            if (bpy.context.scene.render.engine == 'CYCLES'):
                self.material = utils.create_shadeless_cycles_mat()

        scene = bpy.context.scene

        abs_x = 0
        for i in range(len(categories)): # Iterate over each category
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = None
            
            # Create the objects
            location_y = 0
            for j in range(int(cate_count[i]),0,-width): # Creates the rows
                location_x = 0 + abs_x
                for k in range(width): # Creates the items in each row
                    ob = user_object.copy()
                    ob.data = user_object.data
                    ob.animation_data_clear()
                    scene.objects.link(ob)
                    ob.name = ob.name + str(categories[i])
                    ob.location = (location_x, location_y, 0)
                    location_x += ob.dimensions.x + individual_offset
                    objects.append(ob)
                location_y += user_object.dimensions.y + individual_offset
                
            prev_abs_x = abs_x
            abs_x += (user_object.dimensions.x + individual_offset) * width + offset
                
            # Create category labels
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = None
            cate_middle = (prev_abs_x + abs_x - 2*(offset + individual_offset)) / 2
            bpy.ops.object.text_add(location=(cate_middle, -0.7, 0))
            text = bpy.context.object
            text.data.align_x = 'CENTER'
            text.scale = (text.scale.x * 0.15,text.scale.y * 0.15, text.scale.z * 0.15)
            text.name ="label" + str(categories[i])
            text.data.body = categories[i]
            text.active_material = self.material
            
            objects.append(text)

        # Create visualization title
        middle = (((user_object.dimensions.x + individual_offset) * width + offset) * len(categories)-1) / 2
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = None
        bpy.ops.object.text_add(location=(middle, -1.1, 0))
        text = bpy.context.object
        text.data.align_x = 'CENTER'
        text.scale = (text.dimensions.x * 0.30,text.dimensions.y * 0.30, text.dimensions.z * 0.30)
        bpy.ops.object.transform_apply(scale=True)
        if (headers is not None):
            text.name ="title" + str(headers[column])
            text.data.body = headers[column]
        else:
            text.name ="title"
            text.data.body = "Comparison"
        text.active_material = self.material
        objects.append(text)

        # Create Parent Empty
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = None        
        bpy.ops.object.add(radius=0.5, location=(0,text.location.y,0))
        ob = bpy.context.object
        for i in range(len(objects)):
            objects[i].parent = ob
            objects[i].matrix_parent_inverse = ob.matrix_world.inverted()

        utils.normalize_objects(objects, scale=10)    

        return objects
        
    def animate_objects(self):
        duration = self.props.duration
        objects = self.bl_objects
        
        # calculated length of animation per object.
        animate = duration
        offset = float(duration) / float(len(objects))
        
        # Store the current frame so we can restore current frame state later.
        startFrame = bpy.context.scene.frame_current
        
        current_offset = 0
        # Iterate over each data point and animate it.
        for (i, ob) in enumerate(objects):
            bpy.context.scene.frame_current += animate
            ob.keyframe_insert(data_path="scale", index=-1)

            # Insert start keyframe
            bpy.context.scene.frame_current -= animate
            ob.scale = (0,0,0)
            ob.keyframe_insert(data_path="scale", index=-1)
            
            # Offset the next object animation
            current_offset += offset
            if (current_offset > 1):
                bpy.context.scene.frame_current += round(current_offset)
                current_offset = 0

        # Restore frame state    
        bpy.context.scene.frame_current = startFrame
        
    def draw(self, layout, context):
        box = layout.box()
        props = context.scene.import_csv.visprops
        scene = context.scene

        box.prop_search(props, "point_object", scene, "objects",text="Object")

        box.prop(props, 'column')
        box.prop(props, 'split')
        box.prop(props, 'use_animate')
        if (props.use_animate):
            box.prop(props, 'duration')


# HistogramVisualizer creates a histogram (bar chart)
# based on data frequency in a data column.
class HistogramVisualizer():

    dataStore = None
    bl_objects = None
    props = None
    material = None

    def visualize(self, dataStorage):
        self.dataStore = dataStorage
        self.props = bpy.context.scene.import_csv.visprops
        self.bl_objects = self.create_blender_objects()
        if (self.props.use_animate):
            self.animate_objects()

    def create_blender_objects(self):
        headers = self.dataStore.headers
        objects = []
        split = self.props.split
        data = self.dataStore.get_columns()
        column = min(self.props.column, len(data)) -1
        offset = 1
        cate_count, categories = self.dataStore.get_frequencies(column,'DECIMAL',split)
        objects = []
        utils = Utils()
        if (bpy.context.scene.render.engine == 'CYCLES'):
            self.material = utils.create_shadeless_cycles_mat()
    
        # Create a block piece for each category
        # Create labels to put underneath each block
        location_x = 0
        for i in range(len(categories)):
            # Create block
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = None
            bpy.ops.mesh.primitive_plane_add(radius=0.5, location=(0, 0, 0))
            ob = bpy.context.object
            ob.name ="block" + str(categories[i])
            bpy.context.scene.cursor_location = (0,-0.5,0)
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
            ob.scale = (ob.scale.x * 0.35,ob.scale.y * cate_count[i], ob.scale.z)
            bpy.ops.object.transform_apply(scale=True)
            ob.location.x = location_x
            ob.active_material = self.material
            
            # Create labels
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = None
            bpy.ops.object.text_add(location=(location_x, -0.7, 0))
            text = bpy.context.object
            text.data.align_x = 'CENTER'
            text.scale = (text.scale.x * 0.15,text.scale.y * 0.15, text.scale.z * 0.15)
            text.name ="label" + str(categories[i])
            text.data.body = categories[i]
            text.active_material = self.material
            
            objects.append(ob)
            objects.append(text)
            
            location_x += offset

        # Create visualization title
        middle = (offset * len(categories)-1) / 2
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = None
        bpy.ops.object.text_add(location=(middle, -1.1, 0))
        text = bpy.context.object
        text.data.align_x = 'CENTER'
        text.scale = (text.scale.x * 0.30,text.scale.y * 0.30, text.scale.z * 0.30)
        if (headers is not None):
            text.name ="title" + str(headers[column])
            text.data.body = headers[column]
        else:
            text.name ="title"
            text.data.body = "Histogram"
        text.active_material = self.material
        objects.append(text)

        # Create Parent Empty
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = None        
        bpy.ops.object.add(radius=0.25, location=(0,text.location.y,0))
        ob = bpy.context.object
        for i in range(len(objects)):
            objects[i].parent = ob
            objects[i].matrix_parent_inverse = ob.matrix_world.inverted()

        return objects
        
    def animate_objects(self):
        duration = self.props.duration
        objects = self.bl_objects
        
        # Specify an offset
        offset = 1

        # calculated length of animation per object.
        animate = duration
        offset = float(duration) / float(len(objects))
        
        # Store the current frame so we can restore current frame state later.
        startFrame = bpy.context.scene.frame_current

        current_offset = 0
        # Iterate over each data point and animate it.
        for (i, ob) in enumerate(objects):
            bpy.context.scene.frame_current += animate
            ob.keyframe_insert(data_path="scale", index=-1)

            # Insert middle keyframe
            bpy.context.scene.frame_current -= int(animate / 2)
            ob.scale = (ob.scale.x,ob.scale.y*1.5,ob.scale.z)
            ob.keyframe_insert(data_path="scale", index=-1)

            # Insert start keyframe
            bpy.context.scene.frame_current -= int(animate / 2)
            ob.scale = (ob.scale.x,0,ob.scale.z)
            ob.keyframe_insert(data_path="scale", index=-1)
            
            # Offset the next object animation
            current_offset += offset
            if (current_offset > 1):
                bpy.context.scene.frame_current += round(current_offset)
                current_offset = 0

        # Restore frame state    
        bpy.context.scene.frame_current = startFrame
   
    def draw(self, layout, context):
        box = layout.box()
        props = context.scene.import_csv.visprops
        scene = context.scene
        
        box.prop(props, 'column')
        box.prop(props, 'split')
        box.prop(props, 'use_animate')
        if (props.use_animate):
            box.prop(props, 'duration')
  
            
# PieVisualizer creates a pie chart
# based on data frequency in a given column.
class PieVisualizer():

    dataStore = None
    bl_objects = None
    bl_labels = None
    props = None
    material = None

    def visualize(self, dataStorage):
        self.dataStore = dataStorage
        self.props = bpy.context.scene.import_csv.visprops
        self.bl_objects = self.create_blender_objects()
        if (self.props.use_animate):
            self.animate_objects()

    def pie_cutout(self, circle, degrees):
        mesh = circle.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        for v in bm.verts:
            # Loops through the vertices counter-clock wise.
            # Loop until we hit a vertex with index higher than corresponding degree.
            # TODO: Currently assuming index correspond to degrees here
            if (v.index > degrees):
                bm.verts.remove(v)

        center_v = bm.verts.new()
        bm.verts.index_update()
        prev_v = None
        loop_dur = center_v.index

        for v in bm.verts:
            if (prev_v and v.index < loop_dur):
                bm.faces.new([prev_v, v, center_v])
            prev_v = v
        
        bm.to_mesh(mesh)
        bm.free()

    def set_text_labels(self, ob, label, min_rot, max_rot):
            ob.data.align_x = 'CENTER'
            ob.scale = (ob.scale.x * 0.15,ob.scale.y * 0.15, ob.scale.z * 0.15)
            bpy.ops.object.transform_apply(scale=True)
            ob.data.body = label
            ob.rotation_euler = (0,0, (min_rot + (max_rot / 2) ) )
            bpy.ops.transform.translate(value=(0, 1.5, 0), constraint_axis=(False, True, False), constraint_orientation='LOCAL')
            ob.rotation_euler = (0,0,0)

    def create_blender_objects(self):
        headers = self.dataStore.headers
        objects = []
        split = self.props.split
        color = self.props.color
        data = self.dataStore.get_columns()
        column = min(self.props.column, len(data)) -1
        cate_count, categories = self.dataStore.get_frequencies(column,'DEGREES',split)
        utils = Utils()
        if (bpy.context.scene.render.engine == 'CYCLES'):
            self.material = utils.create_shadeless_cycles_mat()
        
        # Create visualization title
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = None
        bpy.ops.object.text_add(location=(0, 1.30, 0))
        text = bpy.context.object
        text.data.align_x = 'CENTER'
        text.scale = (text.scale.x * 0.30,text.scale.y * 0.30, text.scale.z * 0.30)
        if (headers is not None):
            text.name ="title" + str(headers[column])
            text.data.body = headers[column]
        else:
            text.name ="title"
            text.data.body = "Pie Chart"
        text.active_material = self.material
        objects.append(text)
        colors = []
        colors = utils.create_adjacent_colors(color, len(categories))        
        # Create  pie pieces for each category
        # Create labels to put next to the pie pieces
        rotation = 0
        for i in range(len(categories)):
            material = None
            if (bpy.context.scene.render.engine == 'CYCLES'):
                material = utils.create_shadeless_cycles_mat(colors[i],str(i))
            # Create pie chart
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = None
            bpy.ops.mesh.primitive_circle_add(vertices=360, radius=1, fill_type='NOTHING', location=(0, 0, 0))
            circle = bpy.context.object
            circle.name ="pie" + str(categories[i])
            self.pie_cutout(circle, cate_count[i])
            circle.rotation_euler = (0,0, rotation)
            circle.active_material = material

            # Create labels
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = None
            bpy.ops.object.text_add(location=(0, 0, 0))
            text = bpy.context.object
            text.name ="label" + str(categories[i])
            self.set_text_labels(text, categories[i], rotation, radians(cate_count[i]))
            text.active_material = material
            objects.append(circle)
            objects.append(text)

            rotation += radians(cate_count[i])

        # Create Parent Empty
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = None        
        bpy.ops.object.add(radius=0.25, location=(0,0,0))
        ob = bpy.context.object
        for i in range(len(objects)):
            objects[i].parent = ob
            objects[i].matrix_parent_inverse = ob.matrix_world.inverted()

        return objects

    def animate_objects(self):         
        duration = self.props.duration
        objects = self.bl_objects
        
        # Specify an offset
        offset = 1

        # calculated length of animation per object.
        animate = duration
        offset = float(duration) / float(len(objects))
        
        # Store the current frame so we can restore current frame state later.
        startFrame = bpy.context.scene.frame_current
        
        current_offset = 0
        # Iterate over each data point and animate it.
        for (i, ob) in enumerate(objects):            
            bpy.context.scene.frame_current += animate
            ob.keyframe_insert(data_path="rotation_euler", index=-1)
            ob.keyframe_insert(data_path="scale", index=-1)

            # Insert start keyframe
            bpy.context.scene.frame_current -= animate
            ob.rotation_euler = (0,0,radians(-360) + radians(-45) * i+1)
            ob.scale = (0,0,0)
            ob.keyframe_insert(data_path="rotation_euler", index=-1)
            ob.keyframe_insert(data_path="scale", index=-1)
            
            # Offset the next object animation
            current_offset += offset
            if (current_offset > 1):
                bpy.context.scene.frame_current += round(current_offset)
                current_offset = 0

        # Restore frame state    
        bpy.context.scene.frame_current = startFrame


    def draw(self, layout, context):
        box = layout.box()
        props = context.scene.import_csv.visprops
        scene = context.scene
        
        box.prop(props, 'column')
        box.prop(props, 'split')
        box.prop(props, 'color')        
        box.prop(props, 'use_animate')
        if (props.use_animate):
            box.prop(props, 'duration')
        
        
# ScatterVisualizer creates a scatter plot
# by mapping the contents of 1-3 data columns
# to the X, Y or Z location of an object.
class ScatterVisualizer(): 
    
    dataStore = None
    bl_objects = None
    props = None
    material = None

    def visualize(self, dataStorage):
        self.dataStore = dataStorage
        self.props = bpy.context.scene.import_csv.visprops
        self.bl_objects = self.create_blender_objects()
        if (self.props.use_animate):
            self.animate_objects()

    def create_blender_objects(self):
        # Ensure no objects are selected in the scene before proceeding.
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = None
        # Create array to store the blender objects
        objects = []
        utils = Utils()

        data = self.dataStore.get_columns('AS_NUMERIC')
        columnX = min(self.props.column, len(data))-1
        columnY = min(self.props.column2, len(data))-1
        columnZ = min(self.props.column3, len(data))-1
        
        # Iterate over the data and create blender objects for each datapoint.
        # For now we assume the first three columns correspond to X Y Z
        for i in range(len(data[0])):
            # did the user specify an object? otherwise create placeholder objects.
            if self.props.point_object:
                bpy.ops.object.add_named(name=self.props.point_object,linked=True)
            else:
                bpy.ops.object.add(radius=0.1, location=(0,0,0))

            ob = bpy.context.object
            ob.name="dataPoint" + str(i)

            ob.location = (0,0,0)

            if (self.props.use_column):
                ob.location.x = data[columnX][i]
            if (self.props.use_column2):        
                ob.location.y = data[columnY][i]
            if (self.props.use_column3):        
                ob.location.z = data[columnZ][i]
            objects.append(ob) 

        # Create Parent Empty
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = None        
        bpy.ops.object.add(radius=0.25, location=(0,0,0))
        ob = bpy.context.object
        for i in range(len(objects)):
            objects[i].parent = ob
            objects[i].matrix_parent_inverse = ob.matrix_world.inverted()
            
        return objects
    
    def animate_objects(self):
        duration = self.props.duration
        
        # calculated length of animation per object.
        animate = duration
        
        objects = self.bl_objects
        
        # Specify an offset
        offset = 1

        # calculated length of animation per object.    
        offset = float(duration) / float(len(objects))
        
        # Store the current frame so we can restore current frame state later.
        startFrame = bpy.context.scene.frame_current
        
        current_offset = 0
        # Iterate over each data point and animate it.
        for (i, ob) in enumerate(objects):
            # Insert end keyframe
            bpy.context.scene.frame_current += animate
            ob.keyframe_insert(data_path="location", index=-1)

            # Insert start keyframe
            bpy.context.scene.frame_current -= animate
            ob.location = (ob.location.x,0,0)
            ob.keyframe_insert(data_path="location", index=-1)
            
            # Offset the next object animation
            current_offset += offset
            if (current_offset > 1):
                bpy.context.scene.frame_current += round(current_offset)
                current_offset = 0

        # Restore frame state    
        bpy.context.scene.frame_current = startFrame

    def draw(self, layout, context):
        box = layout.box()
        props = context.scene.import_csv.visprops
        scene = context.scene
        
        row = box.row(align=True)
        row.prop(props, 'use_column')
        col = row.column(align=True)
        col.prop(props, 'column')
        if (props.use_column == False):
            col.enabled = False
            
        row = box.row(align=True)
        row.prop(props, 'use_column2')
        col = row.column(align=True)
        col.prop(props, 'column2')
        if (props.use_column2 == False):
            col.enabled = False
            
        row = box.row(align=True)
        row.prop(props, 'use_column3')
        col = row.column(align=True)
        col.prop(props, 'column3')
        if (props.use_column3 == False):
            col.enabled = False

        box.prop_search(props, "point_object", scene, "objects",text="Object")
        box.prop(props, 'use_animate')
        if (props.use_animate):
            box.prop(props, 'duration')


# CSVReader detects the format of CSV files and 
# adds them to a DataStorage object.
class CSVReader():

    filepath = None
    delimiter = ','
    quotechar = ''
    __headers = None

    def __init__(self, f):
        self.filepath = f

    def __detect_delimiter(self, f):    
        commacount = 0
        semicommacount = 0
        tabcount = 0
        f.seek(0)
        for (i,line) in enumerate(f):
            commacount += line.count(',')
            semicommacount += line.count(';')
            tabcount += line.count('\t')
            if (i == 20):
                break
        
        if (commacount > semicommacount and commacount > tabcount):
            self.delimiter = ','
        if (semicommacount > commacount and semicommacount > tabcount):
            self.delimiter = ';'
        if (tabcount > commacount and tabcount > semicommacount):
            self.delimiter = '\t'

    def __detect_quotechar(self,f):
        quotecount = 0
        singlequotecount = 0
        f.seek(0)
        for (i,line) in enumerate(f):
            quotecount += line.count('"')
            singlequotecount += line.count("'")
            if (i == 20):
                break
            
        if (singlequotecount > quotecount):
            self.quotechar = "'"
        else:
            self.quotechar = '"'

    def __detect_labels(self, f):
        non_digits = 0        

        f.seek(0)
        reader = csv.reader(f, delimiter=self.delimiter, quotechar=self.quotechar)
        dataStore = DataStorage()
        
        # does the first line contain non-numerical data?
        # if no, then there are no labels        
        for (i, row) in enumerate(reader):
            dataStore.add_row(row)
            if (i == 20):
                break
        
        data = dataStore.get_columns()
        utils = Utils()
        
        for i in range(len(data)):
            if (utils.is_number(data[i][0]) is False):
                non_digits += 1
                
        if (non_digits == 0):
            self.__headers = None
            return

        # store each piece of non-numerical data of first line in an array.
        # check if _any_ of the next 20 lines contain data from first line
        # if they do, then there are no labels
        matches = 0
        for (x,col) in enumerate(data):
            for (y,val) in enumerate(col):
                if (y == 0):
                    continue
                if (data[x][0] == val):
                    matches += 1

        # if there are more matches than the amount of rows
        # assume that we are dealing with data.
        if (matches > len(data)):
            self.__headers = None
            return

        # first row is non-numerical and unique, assume it's headers
        headers = []
        for (x,col) in enumerate(data):
            headers.append(data[x][0])
            
        self.__headers = headers
        return

    def parse_csv(self, context, filepath):
        f = open(filepath, 'r', encoding='utf-8')
        self.__detect_delimiter(f)
        self.__detect_quotechar(f)
        self.__detect_labels(f)
        
        f.seek(0)
        reader = csv.reader(f, delimiter=self.delimiter, quotechar=self.quotechar)

        # create data structure
        dataStore = DataStorage()

        # If we have detected labels, skip the header
        if (self.__headers is not None):
            dataStore.headers = self.__headers
            reader.__next__()

        # Read the CSV File and store data inside the columns data structure
        for (i, row) in enumerate(reader):
            dataStore.add_row(row)

        # you can access the data using dataStore.get_rows()[x,y]
        return dataStore

# VisualizationProperties is a PropertyGroup which
# stores UI options in the bpy structure so they
# can be drawn by the different visualizers.
class VisualizationProperties(PropertyGroup):
    duration = IntProperty(
            name="Duration",
            description="Duration of the animation (in frames)",
            default=17,
            subtype="TIME",
            )
            
    point_object = StringProperty(
            name="Object",
            description="Choose an object to represent each data point (Optional).",
            )
            
    use_animate = BoolProperty(
            name="Animate",
            description="Animate the data",
            default=True,
            )
            
    column = IntProperty(
        name="Column",
        description="Choose which column of data in the .csv to use",
        min=1,
        default=1,
        )

    use_column = BoolProperty(
            name="X-Axis",
            description="Map CSV column to X Axis",
            default=True,
            )

    column2 = IntProperty(
        name="Column",
        description="Choose which column of data in the .csv to use",
        min=1,
        default=2,
        )

    use_column2 = BoolProperty(
            name="Y-Axis",
            description="Map CSV column to Y Axis",
            default=True,
            )
        
    column3 = IntProperty(
        name="Column",
        description="Choose which column of data in the .csv to use",
        min=1,
        default=3,
        )
        
    use_column3 = BoolProperty(
            name="Z-Axis",
            description="Map CSV column to Z Axis",
            default=True,
            )
        
    split = IntProperty(
        name="Subdivision",
        description="How many categories to split data into",
        min=2,
        default=3,
        )
        
    color = FloatVectorProperty(name="Color", 
                                subtype='COLOR', 
                                default=[0.35,0.49,0.78])      

# ImportCSVProperties is a PropertyGroup
# which instantiates VisualizationProperties
# and stores UI drawn by ImportCSV.
class ImportCSVProperties(PropertyGroup):
    visprops = bpy.props.PointerProperty(type=VisualizationProperties)

    def update_visualizer (other, context):
        # We change visualizer using an index because
        # changing the visualizer itself is not possible from here
        # since objects and string are immutable in python.
        props = bpy.context.scene.import_csv
        if (other.type == 'OPT_SCATTER'):
            props.vis_index = 0
        elif (other.type == 'OPT_PIE'):
            props.vis_index = 1
        elif (other.type == 'OPT_HIST'):
            props.vis_index = 2
        elif (other.type == 'OPT_OBJ'):
            props.vis_index = 3
        return None
        
    type = EnumProperty(
            name="Type",
            description="Choose Visualization Type",
            items=(('OPT_SCATTER', "Scatter Plot", "Position each datapoint in X, Y, Z"),
                   ('OPT_PIE', "Pie Chart", "Create a circle diagram based on frequency"),
                   ('OPT_HIST', "Histogram", "Create a histogram based on frequency"),
                   ('OPT_OBJ', "Object", "Create a custom visualization driven by a user object.")),
            default='OPT_SCATTER',
            update=update_visualizer
            )
    visualizers = [ScatterVisualizer(), PieVisualizer(), HistogramVisualizer(), ObjectVisualizer()]
    vis_index = bpy.props.IntProperty()


# ImportCSV is the Operator class responsible for integrating
# the plug-in with Blender and provides the main flow
# of execution in execute().
# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
class ImportCSV(Operator, ImportHelper):
    """Imports statistical data (.csv) to visualize as graphs."""
    bl_idname = "import_scene.csv"
    bl_label = "Import Statistical Data"

    # ImportHelper mixin class uses this
    filename_ext = {".csv", ".tsv"}

    filter_glob = StringProperty(
            default={"*.csv", ".tsv"},
            options={'HIDDEN'},
            maxlen=255,  # Max internal buffer length, longer would be clamped.
            )
        
    def execute(self, context):   
        reader = CSVReader(self.filepath)
        dataStore = reader.parse_csv(context, self.filepath)
        
        current = context.scene.import_csv.vis_index
        visualizer = context.scene.import_csv.visualizers[current]
        visualizer.visualize(dataStore)
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.import_csv

        box = layout.box()
        box.prop(props, 'type')
        if (props.visualizers):
            props.visualizers[props.vis_index].draw(layout, context)
        

def menu_func_import(self, context):    
    self.layout.operator(ImportCSV.bl_idname, text="Statistical Data (.csv)")

classes = (
    VisualizationProperties,
    ImportCSVProperties,
    ImportCSV
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.Scene.import_csv = PointerProperty(type=ImportCSVProperties)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Operator.import_csv
    
    bpy.types.INFO_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()


