# -*- coding: mbcs -*-
# Do not delete the following import lines
from abaqus import *
from abaqusConstants import *
import displayGroupMdbToolset as dgm
from textRepr import prettyPrint as prettyprint
import __main__
import os
import numpy as np

def logwrite(word):
    logfile = open('log.txt','a')
    logfile.write(word)
    print(word)
    logfile.close()

def Point_extract(line, vertex_coord, Vertex_num_max, coord_x_min, coord_y_min, coord_x_max, coord_y_max):
    # Extract the number of point from the line
    # e.g. Point(1)={161.186,369.387,0,e_def}; -> 1
    line_split = line.split('(')[1].split(')')
    Point_num = int(line_split[0])
    # Find the maximum number of point
    if Point_num > Vertex_num_max:
        Vertex_num_max = Point_num
    # Extract the coordinates of the point
    # e.g. Point(1)={161.186,369.387,0,e_def}; -> 161.186,369.387,0
    line_coord = line_split[1].split('{')[1].split('}')[0].split(',')
    coord_x = float(line_coord[0])/80
    coord_y = float(line_coord[1])/80
    coord_z = float(line_coord[2])/80
    # Find the minimum and maximum coordinates
    if coord_x < coord_x_min:
        coord_x_min = coord_x
    elif coord_x > coord_x_max:
        coord_x_max = coord_x
    elif coord_y < coord_y_min:
        coord_y_min = coord_y
    elif coord_y > coord_y_max:
        coord_y_max = coord_y
    # Save the coordinates of the point
    vertex_coord[Point_num-1] = [coord_x,coord_y,coord_z]
    return vertex_coord, Vertex_num_max, coord_x_min, coord_y_min, coord_x_max, coord_y_max

def Line_edges_extract(line, Edges_vertices, Lines_num_list, Edge_conut):
    Edge_vertices = []
    # If the line contains string 'Line', indicating that the edge is a straight edge
    # Extract the number of edges from the line
    # e.g. Line(1) = {1,2}; -> 1
    line_split = line.split('(')[1].split(')')
    Edge_num = int(line_split[0])
    # Extract the vertices of the edge
    # e.g. Line(1) = {1,2}; -> 1,2
    Edge_vertices_temp = line_split[1].split('{')[1].split('}')[0].split(',')
    for Edge_vertex in Edge_vertices_temp:
        # There are some special expressions need to be considered
        # e.g. Line(1) = {1,2:7,8}; -> 1,2,3,4,5,6,7,8
        if ':' in Edge_vertex:
            num_former = int(Edge_vertex.split(':')[0])
            num_latter = int(Edge_vertex.split(':')[1])
            # In constructing the line, the order of vertices should be followed
            if num_former > num_latter:
                # e.g. 5:2 -> 5,4,3,2
                for i in range(num_former,num_latter-1,-1):
                    Edge_vertices.append(i)
            else:
                # e.g. 2:5 -> 2,3,4,5
                for i in range(num_former,num_latter+1):
                    Edge_vertices.append(i)
        else:
            Edge_vertices.append(int(Edge_vertex))
    # The straight line just can be composed of two vertices
    if len(Edge_vertices) > 2:
        print('The straight line just can be composed of two vertices:%d'%len(Edge_vertices))
        print(line)
    elif len(Edge_vertices) < 2:
        print('The straight line must be composed of two vertices:%d'%len(Edge_vertices))
        print(line)
    # Save the vertices of the edge
    Edges_vertices[Edge_num-1] = Edge_vertices
    Lines_num_list.append(Edge_num-1)
    Edge_conut += 1
    
    return Edges_vertices, Lines_num_list, Edge_conut

def BSpline_edges_extract(line, Edges_vertices, Splines_num_list, Edge_conut):
    Spline_vertices = []
    # If the line contains string 'BSpline', indicating that the edge is a curved edge
    # Extract the number of edges from the line
    # e.g. BSpline(1) = {1,2,3,4}; -> 1
    line_split = line.split('(')[1].split(')')
    Edge_num = int(line_split[0])
    # Extract the vertices of the edge
    # e.g. BSpline(1) = {1,2,3,4}; -> 1,2,3,4
    Spline_vertices_temp = line_split[1].split('{')[1].split('}')[0].split(',')
    for Spline_vertex in Spline_vertices_temp:
        # There are some special expressions need to be considered
        # e.g. BSpline(1) = {1,2:7,8}; -> 1,2,3,4,5,6,7,8
        if ':' in Spline_vertex:
            num_former = int(Spline_vertex.split(':')[0])
            num_latter = int(Spline_vertex.split(':')[1])
            # In constructing the line, the order of vertices should be followed
            if num_former > num_latter:
                # e.g. 5:2 -> 5,4,3,2
                for i in range(num_former,num_latter-1,-1):
                    Spline_vertices.append(i)
            else:
                # e.g. 2:5 -> 2,3,4,5
                for i in range(num_former,num_latter+1):
                    Spline_vertices.append(i)
        else:
            Spline_vertices.append(int(Spline_vertex))
    # Save the vertices of the edge
    Edges_vertices[Edge_num-1] = Spline_vertices
    # Edges_vertices[Edge_num-1] = [Spline_vertices[0],Spline_vertices[-1]]
    Splines_num_list.append(Edge_num-1)
    Edge_conut += 1
    
    return Edges_vertices, Splines_num_list, Edge_conut

def Loop_lines_extract(line, Loop_lines_all, Loop_num_list, Loop_count):
    # Extract the number of line loop from the line
    # e.g. Line Loop(1) = {1,2,3,4}; -> 1
    line_split = line.split('(')[1].split(')')
    Loop_num = int(line_split[0])
    # Extract the vertices of the edge
    # e.g. Line Loop(1) = {1,2,3,4}; -> 1,2,3,4
    Loop_lines_temp = line_split[1].split('{')[1].split('}')[0].split(',')
    Loop_lines = []
    for Loop_line in Loop_lines_temp:
        # There are some special expressions need to be considered
        # e.g. Line Loop(1) = {1,2:7,8}; -> 1,2,3,4,5,6,7,8
        if ':' in Loop_line:
            num_former = int(Loop_line.split(':')[0])-1
            num_latter = int(Loop_line.split(':')[1])-1
            # In constructing the line, the order of vertices should be followed
            if num_former > num_latter:
                # e.g. 5:2 -> 5,4,3,2
                for i in range(num_former,num_latter-1,-1):
                    Loop_lines.append(i)
            else:
                # e.g. 2:5 -> 2,3,4,5
                for i in range(num_former,num_latter+1):
                    Loop_lines.append(i)
        else:
            Loop_lines.append(int(Loop_line)-1)
    # Save the vertices of the edge
    # Splines_vertices[Edge_num-1] = Spline_vertices
    Loop_lines_all[Loop_num-1] = Loop_lines
    Loop_num_list.append(Loop_num)
    Loop_count += 1
    
    return Loop_lines_all, Loop_num_list, Loop_count

def Extract_orientation():
    orientation_file = open('orientation.txt', 'r')
    orientation_file_lines = orientation_file.readlines()[1:]
    # print(orientation_file_lines)
    Phase = []
    phi1  = []
    phi2  = []
    phi3  = []
    for line in orientation_file_lines:
        line = line.strip('\n')
        line = line.split('\t')

        Phase.append(line[1])
        phi1.append(float(line[2]))
        phi2.append(float(line[3]))
        phi3.append(float(line[4]))
    
    return Phase, phi1, phi2, phi3
def find_center(face_vertices, vertex_coord, i):
    # Calculating the centroid of polygon (https://www.zhihu.com/question/337823261)
    # Shoelace Theorem to calculate the area of the polygon (https://zhuanlan.zhihu.com/p/110025234)
    area_sum = 0
    term_x_sum = 0
    term_y_sum = 0
    for i in range(len(face_vertices)):
        coord_x_i = vertex_coord[face_vertices[i]][0]
        coord_y_i = vertex_coord[face_vertices[i]][1]
        if i+1 > len(face_vertices)-1:
            coord_x_i_1 = vertex_coord[face_vertices[0]][0]
            coord_y_i_1 = vertex_coord[face_vertices[0]][1]
        else:
            coord_x_i_1 = vertex_coord[face_vertices[i+1]][0]
            coord_y_i_1 = vertex_coord[face_vertices[i+1]][1]
        area_sum += 0.5*(coord_x_i*coord_y_i_1-coord_x_i_1*coord_y_i)
        term_x_sum += (coord_x_i+coord_x_i_1)*(coord_x_i*coord_y_i_1-coord_x_i_1*coord_y_i)
        term_y_sum += (coord_y_i+coord_y_i_1)*(coord_x_i*coord_y_i_1-coord_x_i_1*coord_y_i)
    coord_x_center = term_x_sum/(6*area_sum)
    coord_y_center = term_y_sum/(6*area_sum)
    return [coord_x_center, coord_y_center]



def euler_to_rotation_matrix(euler_angles):
    """
    Convert Euler angles to rotation matrix.

    :param euler_angles: array-like, shape (3,).
        Euler angles in radians.
    :return: array-like, shape (3, 3).
        Rotation matrix.
    """
    roll, pitch, yaw = euler_angles
    Rx = np.array([[1, 0, 0],
                   [0, np.cos(roll), -np.sin(roll)],
                   [0, np.sin(roll), np.cos(roll)]])
    Ry = np.array([[np.cos(pitch), 0, np.sin(pitch)],
                   [0, 1, 0],
                   [-np.sin(pitch), 0, np.cos(pitch)]])
    Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0],
                   [np.sin(yaw), np.cos(yaw), 0],
                   [0, 0, 1]])
    R = np.dot(Rz, np.dot(Ry, Rx))
    return R


if os.path.exists('log.txt'):
    os.remove('log.txt')
logwrite('*'*70 + '\n' +
        '*' + '{0:^68}'.format('Transform Geo to Abaqus model') + '*' + '\n' +
        '*'*70 + '\n')
# ********************************************************************** #
#get current working directory
WorkingDirectory = os.getcwd()
#change current working directory to current working directory
os.chdir(WorkingDirectory)
# ********************************************************************** #
#                        Inputing the .geo file name                     #
# ********************************************************************** #
# Open the file
GeoFile_Name  = "titanium"
crack_width = 0.01
crack_length = 0.2
GeoFile       = open("%s.geo"%GeoFile_Name,'r')
GeoFile_lines = GeoFile.readlines()
GeoFile.close()
# ********************************************************************** #
#       Extract the orientation, vertices and edges information          #
# ********************************************************************** #
# Initialize the variables
# ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! 
# Postulate that the number of vertices is less than 1e7, 
# if not, change the value of 1e7 to a larger number
# ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! 
vertex_coord     = [[]]*1*10**7
Edges_vertices   = [[]]*1*10**7
Splines_vertices = [[]]*1*10**7
Loop_lines_all   = [[]]*1*10**7
Lines_num_list   = []
Splines_num_list = []
Loop_lines       = []
Loop_num_list    = []
Loop_count       = 0
coord_x_min      = 0
coord_y_min      = 0
coord_x_max      = 0
coord_y_max      = 0


logwrite('{0:-^68}'.format('Extract grain boundaries information from Geo file') + '\n')
Vertex_num_max  = 0
# Loop over the lines in the .geo file
Edge_conut = 0
for line in GeoFile_lines:
    # ****************************************************************** #
    #                         Extract the vertices                       #
    # ****************************************************************** #
    if 'Loop' in line:
        if 'Closed Loops' in line:
            continue
        # Extract the Line loop
        [Loop_lines_all, Loop_num_list, Loop_count] = Loop_lines_extract(
            line, Loop_lines_all, Loop_num_list, Loop_count)
    # ****************************************************************** #
    #                         Extract the vertices                       #
    # ****************************************************************** #
    elif 'Point' in line:
        # Extract the number of point
        [vertex_coord, Vertex_num_max, coord_x_min, coord_y_min, coord_x_max, coord_y_max] = Point_extract(
            line, vertex_coord, Vertex_num_max, coord_x_min, coord_y_min, coord_x_max, coord_y_max)
    # ****************************************************************** #
    #                           Extract the edges                        #
    # ****************************************************************** #
    elif 'Line' in line:
        # Extract Line edges
        [Edges_vertices, Lines_num_list, Edge_conut] = Line_edges_extract(
            line, Edges_vertices, Lines_num_list, Edge_conut)
    elif 'BSpline' in line:
        # Extract BSpline edges
        [Edges_vertices, Splines_num_list, Edge_conut] = BSpline_edges_extract(
            line, Edges_vertices, Splines_num_list, Edge_conut)

# print(Loop_lines_all[0:Loop_count])
# print(Loop_count)
# print(Lines_num_list)
# print(Splines_num_list)
# Extract the orientation information from the orientation.txt file
[Phase, phi1, phi2, phi3] = Extract_orientation()
logwrite('Extract successfully' + '\n')
# ********************************************************************** 
# In the following, the edges and splines will be used to create the     
# sketch of the polycrystalline diagram.                                 
# Besides, a medium and a crack will be inserted.                        
# The medium is around the polycrystalline region.                       
# The crack runs through the medium and the crack tip contacts the marge 
#  of the base shell.                                                    
#                      Base shell                                   
#       ----------------------------------------
#       |                                      |
#       |               Medium                 |
#       |              -----------------       |
#       |              |               |       |
#       |    Crack     |Polycrystalline|       |
#       -------------->|     region    |       |
#       |              |               |       |
#       |              |               |       |
#       |              -----------------       |
#       |                                      |
#       |                                      |
#       ----------------------------------------

# ********************************************************************** #
#                      First, create the base shell                      #
# ********************************************************************** #
logwrite('{0:-^68}'.format('Creating geometry features') + '\n')
myModel = mdb.models["Model-1"]
sketch_base = myModel.ConstrainedSketch(name='__profile__', sheetSize=50.0)
# Defining the vertices of the base shell, and offset from the polycrystalline region
#
# Point7 |<-----------------Length--------------------->| Point6
#        --------------------------------------------------
#        |                                              | ^
#        |                                              | |
#        |         Point10                              | |
#        |       ( Circle1 )         Medium             | |
#        |                     -----------------        | |
#        |                     |               |        | |
#        |               Point9|               |        | |
#  Point8--------------------\ |               |        | |
#                  Crack tip  \|Polycrystalline|        | |
#                    Point1   /|    region     |        | |
#  Point3--------------------/ |               |        | Width
#        |               Point2|               |        | |
#        |  Crack length       |               |offset_x| |
#        |<------------------->-----------------<------>| |
#        |         Point11     ^                        | |
#        |       ( Circle2 )   |                        | |
#        |                     |offset_y                | |
#        |                     |                        | |
#        --------------------------------------------------
#     Point4                                    Point5
# The crack is sketched under the Standard GB/T 6398-2017
#
#        |<------Crack Length----->|
#     -------------------------\   |
#      ^ |                      \  |
#      | |                       \ |
# Crack| |                        \|
# Width| |                        /|
#      | |                       / |   
#      | |                      /  |
#      ------------------------/   |
#                              |<->|
#                            Crack_width
# Initial the parameters
# PR_length = length of the polycrystalline region
# PR_width  = width of the polycrystalline region
PR_length = coord_x_max - coord_x_min
PR_width  = coord_y_max - coord_y_min
offset_x = 3
offset_y = 3
Length   = 30
Width    = 30
Crack_length = 10
Crack_width  = 1.5
# The length of the base shell must longer than the polycrystalline region
# and so must the width relative to the polycrystalline region
if Length < PR_length + Crack_length:
    # If the length is shorter than the polycrystalline region, then the length 
    # is set to be the length of polycrystalline region plus double offset
    Length = PR_length + Crack_length + offset_x
    print('The length of the base shell is short and have been set to be the length of polycrystalline region plus double offset')
if Width < PR_width:
    # If the width is shorter than the polycrystalline region, then the width
    # is set to be the width of polycrystalline region plus double offset
    Width = PR_width + Crack_length + offset_y
    print('The width of the base shell is short and have been set to be the width of polycrystalline region plus double offset')
# ********************************************************************** #
#                          Create the base shell                         #
# ********************************************************************** #
Point_1 = [coord_x_min                            , (coord_y_min+coord_y_max)/2          ,0]
Point_2 = [Point_1[0] - Crack_width               , Point_1[1] - Crack_width/2.0         ,0]
Point_3 = [Point_2[0] - Crack_length-Crack_width  , Point_2[1]                           ,0]
Point_4 = [Point_3[0]                             , Point_3[1] - (Width - Crack_width)/2 ,0]
Point_5 = [Point_4[0] + Length                    , Point_4[1]                           ,0]
Point_6 = [Point_5[0]                             , Point_5[1] + Width                   ,0]
Point_7 = [Point_6[0] - Length                    , Point_6[1]                           ,0]
Point_8 = [Point_7[0]                             , Point_7[1] - (Width - Crack_width)/2 ,0]
Point_9 = [Point_8[0] + Crack_length+Crack_width  , Point_8[1]                           ,0]
# sketch_base.rectangle(point1=(Point_1[0], Point_1[1]), point2=(Length, Width))
# sketch the base shell according the order:
# Point_1 -> Point_2 -> Point_3 -> Point_4 -> Point_5 -> 
# -> Point_6 -> Point_7 -> Point_8 -> Point_9 -> Point_1
sketch_base.Line(point1=(Point_1[0], Point_1[1]), point2=(Point_2[0], Point_2[1]))
sketch_base.Line(point1=(Point_2[0], Point_2[1]), point2=(Point_3[0], Point_3[1]))
sketch_base.Line(point1=(Point_3[0], Point_3[1]), point2=(Point_4[0], Point_4[1]))
sketch_base.Line(point1=(Point_4[0], Point_4[1]), point2=(Point_5[0], Point_5[1]))
sketch_base.Line(point1=(Point_5[0], Point_5[1]), point2=(Point_6[0], Point_6[1]))
sketch_base.Line(point1=(Point_6[0], Point_6[1]), point2=(Point_7[0], Point_7[1]))
sketch_base.Line(point1=(Point_7[0], Point_7[1]), point2=(Point_8[0], Point_8[1]))
sketch_base.Line(point1=(Point_8[0], Point_8[1]), point2=(Point_9[0], Point_9[1]))
sketch_base.Line(point1=(Point_9[0], Point_9[1]), point2=(Point_1[0], Point_1[1]))
sketch_base.CircleByCenterPerimeter(center=(Point_1[0] - 5.5 , Point_1[1] + 6.93), point1=(Point_1[0] - 5.5, Point_1[1] + 6.93 + 6.3/2))
sketch_base.CircleByCenterPerimeter(center=(Point_1[0] - 5.5 , Point_1[1] - 6.93), point1=(Point_1[0] - 5.5, Point_1[1] - 6.93 + 6.3/2))
mypart = myModel.Part(name='Part-1', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
mypart.BaseShell(sketch=sketch_base)

# ********************************************************************** #
#       Create the grain boundaries by partition the base shell          #
#                    grain boundaries obtained above
# ********************************************************************** #
# ********Create the grain boundraies based on the straight edge******** #
print('Creating grains')
mypart = myModel.parts['Part-1']
Sketch_GB = myModel.ConstrainedSketch(name='__profile__', sheetSize=500.0, gridSpacing=10)
Sketch_GB.setPrimaryObject(option=SUPERIMPOSE)
mypart.projectReferencesOntoSketch(sketch=Sketch_GB, filter=COPLANAR_EDGES)
face_vertices_all = [[]]*Loop_count
center_all        = [[]]*Loop_count
for i in range(Loop_count):
    Loop_lines = Loop_lines_all[i]
    # print(Loop_lines)
    face_vertices = []
    # Creating the material based on phase
    mdb.models['Model-1'].Material(name='Homogeneous')
    mdb.models['Model-1'].materials['Homogeneous'].UserMaterial(
        mechanicalConstants=(10000000000.0, 0.33, 0))
    try:
        # If there have exist the same material, skip the process
        material_name = Phase[i] + str(i+1)
        mdb.models['Model-1'].Material(name=material_name)
        mdb.models['Model-1'].materials[material_name].UserMaterial(
        mechanicalConstants=(10000000000.0, 0.33, i+1))
    except:
        pass
    for line_num in Loop_lines:
        if abs(line_num) in Lines_num_list:
            # This is a straight edge
            Edge = Edges_vertices[abs(line_num)]
            # Store the vertices of the face
            face_vertices.append(Edge[0]-1)
            face_vertices.append(Edge[1]-1)
            vertex_coord_1_x = vertex_coord[Edge[0]-1][0]
            vertex_coord_1_y = vertex_coord[Edge[0]-1][1]
            vertex_coord_2_x = vertex_coord[Edge[1]-1][0]
            vertex_coord_2_y = vertex_coord[Edge[1]-1][1]
            try:
                # Create the sketch of the grain boundary by straight edge
                Sketch_GB.Line(point1=(vertex_coord_1_x,vertex_coord_1_y), point2=(vertex_coord_2_x,vertex_coord_2_y))
                # Remove the line number that has been used
                Lines_num_list.remove(abs(line_num))
                # print(abs(line_num))
            except:
                print('There is something wrong when creating the sketch by straight edge')
                print(Edge)
        if abs(line_num) in Splines_num_list:
            # This is a spline edge
            points_x = []
            points_y = []
            Spline_vertices = Edges_vertices[abs(line_num)]
            # Loop over the vertices of the spline
            for Spline_vertex in Spline_vertices:
                # Get the coordinates of the vertex and append to the string
                Spline_vertex_x = vertex_coord[Spline_vertex-1][0]
                Spline_vertex_y = vertex_coord[Spline_vertex-1][1]
                points_x.append(Spline_vertex_x)
                points_y.append(Spline_vertex_y)
                # There are too many vertices in the spline, so we only use the first 5 vertices
                if Spline_vertices.index(Spline_vertex) <= 5:
                    face_vertices.append(Spline_vertex-1)
            try:
                Sketch_GB.Spline(points=zip(points_x,points_y))
                Splines_num_list.remove(abs(line_num))
                # print(abs(line_num))
                # Sketch_GB.Line(point1=(points_x[0],points_y[0]), point2=(points_x[-1],points_y[-1]))
            except:
                print('There is something wrong when creating the sketch by spline edge')
                print(Spline_vertices)
                print(points_x)
                print(points_y)
    face_vertices_all[i] = face_vertices
    center = find_center(face_vertices, vertex_coord, i)
    center_all[i] = [center[0], center[1]]
    # print(center)

    f = mypart.faces
    # Find the base face based on the point_1 mentioned above
    base_face = f.findAt(((Point_4[0], Point_4[1], 0), ) )
    
    # for face in f:
    try:
        # Partition the base face by the sketch
        new_face = mypart.PartitionFaceBySketch(faces=base_face, sketch=Sketch_GB)
        Sketch_GB.unsetPrimaryObject()
        # print('Partitioning the base shell successfully')
        session.viewports['Viewport: 1'].setValues(displayedObject=mypart)
    except:
        print('Grain %s: Partitioning failed'%(i+1))
    


    # According to the centroid of the face, create a relavent set for assigning the orientation
    face = f.findAt(((center[0], center[1], 0), ) )
    region_grain = mypart.Set(faces=face, name='Grain_%s'%(i+1))

    # print('Creating the set successfully')
    # prettyprint(f[0:1])
    
    
    mdb.models['Model-1'].HomogeneousSolidSection(name='Grain-%s'%(i+1), 
                    material=material_name, thickness=None)

    # print('Creating the section successfully')
    mypart.SectionAssignment(region=region_grain, sectionName='Grain-%s'%(i+1), offset=0.0, 
        offsetType=MIDDLE_SURFACE, offsetField='', 
        thicknessAssignment=FROM_SECTION)
    
    
    # Creating local coordinate system
    Local_sys_exist = 0
    if Local_sys_exist == 1:
        Global_coord_sys = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        Rotation_matrix = euler_to_rotation_matrix([phi1[i], phi2[i], phi3[i]])
        Local_coord_sys = np.dot(Rotation_matrix, Global_coord_sys)
        axis_x = np.transpose(Local_coord_sys)[0]
        axis_y = np.transpose(Local_coord_sys)[1]
        mypart.DatumCsysByThreePoints(name='Datum csys-%s'%(i+1), coordSysType=CARTESIAN, origin=(
            center[0], center[1], 0.0), point1=(axis_x[0], axis_x[1], 0), point2=(axis_y[0], axis_y[1], 0))
        datums = mdb.models['Model-1'].parts['Part-1'].datums.keys()
        orientation = mdb.models['Model-1'].parts['Part-1'].datums[datums[-1]]
        mdb.models['Model-1'].parts['Part-1'].MaterialOrientation(region=region_grain, 
            orientationType=SYSTEM, axis=AXIS_3, localCsys=orientation, 
            fieldName='', additionalRotationType=ROTATION_NONE, angle=0.0, 
            additionalRotationField='', stackDirection=STACK_3)
    # if i == 4:
    #     break
    

    
    milestone('Creating curved edge',i+1/Loop_count)
# Creating the section and assign material property for homogeneous region
base_face = f.findAt(((Point_4[0], Point_4[1], 0), ) )
region_homo = mypart.Set(faces=base_face, name='Homogeneous_region')
mdb.models['Model-1'].HomogeneousSolidSection(name='Homogeneous_section', 
                material='Homogeneous', thickness=None)
mypart.SectionAssignment(region=region_homo, sectionName='Homogeneous_section', offset=0.0, 
    offsetType=MIDDLE_SURFACE, offsetField='', 
    thicknessAssignment=FROM_SECTION)
if Local_sys_exist == 1:
    mdb.models['Model-1'].parts['Part-1'].MaterialOrientation(region=region_homo, 
        orientationType=GLOBAL, axis=AXIS_3, 
        additionalRotationType=ROTATION_NONE, localCsys=None, fieldName='', 
        stackDirection=STACK_3)
logwrite('{0:-^68}'.format('Finished successfully') + '\n')
del myModel.sketches['__profile__']
# ********************************************************************** #
#                       Creating the display group                       #
# ********************************************************************** #
if Local_sys_exist == 1:
    # Select all datums
    group = []
    datums = mdb.models['Model-1'].parts['Part-1'].datums.keys()
    for datum_key in datums:
        datum = mdb.models['Model-1'].parts['Part-1'].datums[datum_key]
        group.append(datum)
    leaf = dgm.LeafFromDatums(group)
    # Create the display group 'Datums_add' for datums visible
    session.viewports['Viewport: 1'].partDisplay.displayGroup.add(leaf=leaf)
    dg = session.viewports['Viewport: 1'].partDisplay.displayGroup
    dg = session.DisplayGroup(name='Datums_add', objectToCopy=dg)
    session.viewports['Viewport: 1'].partDisplay.setValues(visibleDisplayGroups=(
        dg, ))
    # Create the display group 'Datums_remove' for datums invisible
    session.viewports['Viewport: 1'].partDisplay.displayGroup.remove(leaf=leaf)
    dg = session.viewports['Viewport: 1'].partDisplay.displayGroup
    dg = session.DisplayGroup(name='Datums_remove', objectToCopy=dg)
    session.viewports['Viewport: 1'].partDisplay.setValues(visibleDisplayGroups=(
        dg, ))
# ********************************************************************** #
#                       Output variables into file                       #
# ********************************************************************** #
# Output the centroid of grains for check
with open('Grains_centroid.txt','w') as centroid_file:
    centroid_file.write('Grain_ID' + '\t' + 'Coord_x' + '\t' + 'Coord_y' + '\n')
    for index,centroid in enumerate(center_all):
        if centroid != []:
            centroid_file.write(str(index+1) + '\t' + str(centroid[0]) + '\t' + str(centroid[1]) + '\n')
# ********************************************************************** #
#                      The script runs successfully                      #
# ********************************************************************** #
logwrite('{0:*^68}'.format('Successfully created the model') + '\n')