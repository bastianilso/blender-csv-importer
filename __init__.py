# <pep8 compliant>
bl_info = {  
 "name": "Import Statistical Data (*.csv)",  
 "author": "Bastian Ilso (bastianilso)",  
 "version": (0, 1),  
 "blender": (2, 7, 7),  
 "location": "File > Import > Import Statistical Data (*.csv)",  
 "description": "Import, visualize and animate data stored as *.csv",  
 "warning": "",  
 "wiki_url": "",  
 "tracker_url": "https://github.com/bastianilso/blender-csv-importer",  
 "category": "Import-Export"}

# Usage: call when you want to print contents of an object
def dump(obj):
   for attr in dir(obj):
       if hasattr( obj, attr ):
           print( "obj.%s = %s" % (attr, getattr(obj, attr)))

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, PointerProperty
from bpy.types import Operator, PropertyGroup
import csv
import bmesh
from math import radians, degrees
from mathutils import Vector

class DataStorage():
    
    data = None

    def __init__(self, d = None):
        self.data = d
    
    def add_row(self, row):        
        # TODO: zero-pad all entries if the length of a row exceeds already added rows.
        # Use the length of the first row to determine amount of columns
        if (self.data == None):
            self.data = []
            self.data = [[] for i in range(len(row))]

        # Append values from each parsed row into the array.
        for (j,v) in enumerate(row):
            self.data[j].append(float(v))
    
    def get_columns(self):
        return self.data
    
    def get_frequencies(self, column, split, output_type):
        # TODO: Detect whether column is string or numerical
        # TODO: if non-numeric: count the amount of identical values.
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
            #print("category: " + categories[i] + ", cate_count is: " + str(cate_count[i]))
                                
        total = sum(c for c in cate_count)   
        for i in range(len(cate_count)):
            #print(str(cate_count[i] / total) + "%")
            cate_count[i] = cate_count[i] / total
            if (output_type == 'DEGREES'):
                cate_count[i] = round(cate_count[i] * 360,2)

        return (categories, cate_count)


        
# TODO: Define toString method

# TODO: Make Abstract Visualizer Class.

class HistogramVisualizer():

    dataStore = None
    bl_objects = None
    props = None

    def visualize(self, dataStorage):
        self.dataStore = dataStorage
        self.props = bpy.context.scene.import_csv.visprops
        self.bl_objects = self.create_blender_objects()
        if (self.props.use_animate):
            self.animate_objects()

    def block_scale(self, block, percentage):
        # Set origin to the bottom
        # Scale along y-axis by percentage
        return block
    

    def create_blender_objects(self):
        print("create_blender_objects..")

        objects = []
        split = self.props.split
        column = self.props.column -1
        offset = 1
        # TODO: Detect whether column is string or numerical
        # TODO: if non-numeric: count the amount of identical values.
        categories, cate_count = self.dataStore.get_frequencies(column,split,'PERCENTAGE')
        #print(str(cate_count))
        
        # Create  pie pieces for each category
        # Create labels to put next to the pie pieces
        location_x = 0
        for i in range(len(categories)):
            # Create pie chart
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
            
            # Create labels
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = None
            bpy.ops.object.text_add(location=(location_x, -0.7, 0))
            text = bpy.context.object
            text.data.align_x = 'CENTER'
            text.scale = (text.scale.x * 0.15,text.scale.y * 0.15, text.scale.z * 0.15)
            text.name ="label" + str(categories[i])
            text.data.body = categories[i]
            
            objects.append(ob)
            objects.append(text)
            
            location_x += offset

        return objects
        

    def animate_objects(self):
        print("running animate_objects..")  

        duration = self.props.duration
        objects = self.bl_objects
        
        # Specify an offset
        offset = 1

        # calculated length of animation per object.
        animate = duration - (offset * len(objects))
        
        # Store the current frame so we can restore current frame state later.
        startFrame = bpy.context.scene.frame_current
        
        print ("duration in frames: " + str(duration))
        print("amount of objects: " + str(len(objects)))
        print("offset per object: " + str(offset))
        print("animate per object: " + str(animate))

        # Iterate over each data point and animate it.
        for (i, ob) in enumerate(objects):
            print("----")
            print("current frame is: " + str(bpy.context.scene.frame_current))
            print("current offset is: " + str(offset))
            print("current duration is: " + str(animate))
            print("start frame is: " + str(bpy.context.scene.frame_current))
            print("end frame is: " + str(bpy.context.scene.frame_current + animate))
            
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
            bpy.context.scene.frame_current += offset

        # Restore frame state    
        bpy.context.scene.frame_current = startFrame


    
    def draw(self, layout, context):
        layout.label("test")
        box = layout.box()
        props = context.scene.import_csv.visprops
        scene = context.scene
        
        box.prop(props, 'column')
        box.prop(props, 'split')
        box.prop(props, 'use_animate')
        if (props.use_animate):
            box.prop(props, 'duration')
            

class PieVisualizer():

    dataStore = None
    bl_objects = None
    bl_labels = None
    props = None

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
                #print('creating triangle: ' + str(v.index) + ': ' + str(v.co) + ', ' + str(prev_v.index) + ':' + str(prev_v.co) + ', ' + str(center_v.index) + ':' + str(center_v.co))
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
        print("create_blender_objects..")

        objects = []
        split = self.props.split
        column = self.props.column -1
        categories, cate_count = self.dataStore.get_frequencies(column,split,'DEGREES')
        #print(str(cate_count))
        # Create  pie pieces for each category
        # Create labels to put next to the pie pieces
        rotation = 0
        for i in range(len(categories)):
            # Create pie chart
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = None
            bpy.ops.mesh.primitive_circle_add(vertices=360, radius=1, fill_type='NOTHING', location=(0, 0, 0))
            circle = bpy.context.object
            circle.name ="pie" + str(categories[i])
            self.pie_cutout(circle, cate_count[i])
            circle.rotation_euler = (0,0, rotation)

            # Create labels
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active = None
            bpy.ops.object.text_add(location=(0, 0, 0))
            text = bpy.context.object
            text.name ="label" + str(categories[i])
            self.set_text_labels(text, categories[i], rotation, radians(cate_count[i]))
            
            objects.append(circle)
            objects.append(text)
            
            rotation += radians(cate_count[i])

        return objects

    def animate_objects(self):
        print("running animate_objects..")             

        duration = self.props.duration
        objects = self.bl_objects
        
        # Specify an offset
        offset = 1

        # calculated length of animation per object.
        animate = duration - (offset * len(objects))
        
        # Store the current frame so we can restore current frame state later.
        startFrame = bpy.context.scene.frame_current
        
        print ("duration in frames: " + str(duration))
        print("amount of objects: " + str(len(objects)))
        print("offset per object: " + str(offset))
        print("animate per object: " + str(animate))

        # Iterate over each data point and animate it.
        for (i, ob) in enumerate(objects):
            print("----")
            print("current frame is: " + str(bpy.context.scene.frame_current))
            print("current offset is: " + str(offset))
            print("current duration is: " + str(animate))
            print("start frame is: " + str(bpy.context.scene.frame_current))
            print("end frame is: " + str(bpy.context.scene.frame_current + animate))
            
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
            bpy.context.scene.frame_current += offset

        # Restore frame state    
        bpy.context.scene.frame_current = startFrame


    def draw(self, layout, context):
        layout.label("test")
        box = layout.box()
        props = context.scene.import_csv.visprops
        scene = context.scene
        
        box.prop(props, 'column')
        box.prop(props, 'split')
        box.prop(props, 'use_animate')
        if (props.use_animate):
            box.prop(props, 'duration')
        

class ScatterVisualizer(): 
    
    dataStore = None
    bl_objects = None
    props = None

    def visualize(self, dataStorage):
        self.dataStore = dataStorage
        self.props = bpy.context.scene.import_csv.visprops
        self.bl_objects = self.create_blender_objects()
        if (self.props.use_animate):
            self.animate_objects()
        
    def create_blender_objects(self):
        print("create_blender_objects..")

        # Ensure no objects are selected in the scene before proceeding.
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = None

        data = self.dataStore.get_columns()

        # Create array to store the blender objects
        objects = []
        
        # Iterate over the data and create blender objects for each datapoint.
        # For now we assume the first three columns correspond to X Y Z
        for i in range(len(data[0])):
            loc = (data[0][i], data[1][i], data[2][i])
            
            # did the user specify an object? otherwise create placeholder objects.
            if self.props.point_object:
                bpy.ops.object.add_named(name=self.props.point_object,linked=True)
            else:
                bpy.ops.object.add(radius=0.1)
                
            ob = bpy.context.object
            ob.name="dataPoint" + str(i)
            ob.location=loc
            objects.append(ob)
            
        return objects
    
    def animate_objects(self):
        print("running animate_objects..")
        
        duration = self.props.duration
        objects = self.bl_objects
        
        # Specify an offset
        offset = 1

        # calculated length of animation per object.    
        animate = duration - (offset * len(objects))
        
        # Store the current frame so we can restore current frame state later.
        startFrame = bpy.context.scene.frame_current
        
        print ("duration in frames: " + str(duration))
        print("amount of objects: " + str(len(objects)))
        print("offset per object: " + str(offset))
        print("animate per object: " + str(animate))

        # Iterate over each data point and animate it.
        for (i, ob) in enumerate(objects):
            print("----")
            print("current frame is: " + str(bpy.context.scene.frame_current))
            print("current offset is: " + str(offset))
            print("current duration is: " + str(animate))
            print("start frame is: " + str(bpy.context.scene.frame_current))
            print("end frame is: " + str(bpy.context.scene.frame_current + animate))
            
            # Insert end keyframe
            bpy.context.scene.frame_current += animate
            ob.keyframe_insert(data_path="location", index=-1)

            # Insert start keyframe
            bpy.context.scene.frame_current -= animate
            ob.location = (ob.location.x,0,0)
            ob.keyframe_insert(data_path="location", index=-1)
            
            # Offset the next object animation
            bpy.context.scene.frame_current += offset

        # Restore frame state    
        bpy.context.scene.frame_current = startFrame

    def draw(self, layout, context):
        layout.label("test")
        box = layout.box()
        props = context.scene.import_csv.visprops
        scene = context.scene

        box.prop_search(props, "point_object", scene, "objects",text="Object")
        # TODO: Expose how things should be mapped also
        box.prop(props, 'use_animate')
        if (props.use_animate):
            box.prop(props, 'duration')
            # TODO: Expose Animation Type    
    
class CSVReader():

    filepath = None
    delimiter = ''
    quotechar = ''
    __headers = None

    def __init__(self, f):
        self.filepath = f
        # detect delimiter
        # detect quotechar
        # detect_labels

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
            
        print('quotecount ' + str(quotecount))
        print('singlequotecount ' + str(singlequotecount))
        if (singlequotecount > quotecount):
            self.quotechar = "'"
        else:
            self.quotechar = '"'

    def __detect_labels(self):
        self.__headers = None
        # does the file contain numerical data?
            #no, then expose manual boolean for detecting labels.
        # is the first line strings or numerical data?
            # if it is strings, then assume it is labels. 

    def parse_csv(self, context, filepath):
        print("running parse_csv...")
        f = open(filepath, 'r', encoding='utf-8')
        self.__detect_delimiter(f)
        self.__detect_quotechar(f)
        f.seek(0)
        reader = csv.reader(f, delimiter=self.delimiter, quotechar=self.quotechar)
        # TODO: Come up with a way to detect and skip possible headers using this.
        #if (headers):
            #reader.__next__()

        # Read the CSV File and store data inside a columns data structure
        columns = []
        dataStore = DataStorage()
        for (i, row) in enumerate(reader):
            print(row)
            dataStore.add_row(row)

        # you can access the data using dataStore.get_rows()[x,y]
        return dataStore

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
            
    # TODO: Adapt UI depending on the file selected
    #       and use actual header names to choose column
    column = IntProperty(
        name="Column",
        description="Which column to create pie chart from",
        min=1,
        default=1,
        )
        
    split = IntProperty(
        name="Subdivision",
        description="How many categories to split data into",
        min=2,
        default=3,
        )

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
        return None
        
    type = EnumProperty(
            name="Type",
            description="Choose Visualization Type",
            items=(('OPT_SCATTER', "Scatter Plot", "Position each datapoint in X, Y, Z"),
                   ('OPT_PIE', "Pie Chart", "Description two"),
                   ('OPT_HIST', "Histogram", "Description two")),
            default='OPT_SCATTER',
            update=update_visualizer
            )
    visualizers = [ScatterVisualizer(), PieVisualizer(), HistogramVisualizer()]
    vis_index = bpy.props.IntProperty()


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.

class ImportCSV(Operator, ImportHelper):
    """Imports statistical data (.csv) to visualize as graphs."""
    # Important since its how bpy.ops.import_scene.csv is constructed
    bl_idname = "import_scene.csv"
    bl_label = "Import Statistical Data"

    # ImportHelper mixin class uses this
    filename_ext = ".csv"

    filter_glob = StringProperty(
            default="*.csv",
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
    
    # test call
    bpy.ops.import_scene.csv('INVOKE_DEFAULT')


