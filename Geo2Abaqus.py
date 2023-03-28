# -*- coding: mbcs -*-
# Do not delete the following import lines
from abaqus import *
from abaqusConstants import *
import __main__
import os

# ********************************************************************** #
#get current working directory
WorkingDirectory = os.getcwd()
#change current working directory to current working directory
os.chdir(WorkingDirectory)
# ********************************************************************** #
#                        Inputing the .geo file name                     #
# ********************************************************************** #
# Open the file
TessFile_Name  = "titanium"
crack_width = 0.01
crack_length = 0.2
TessFile       = open("%s.geo"%TessFile_Name,'r')
TessFile_lines = TessFile.readlines()
TessFile.close()
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
coord_x_min = 0
coord_y_min = 0
coord_x_max = 0
coord_y_max = 0
Vertex_mum_max  = 0
# Loop over the lines in the .geo file
for line in TessFile_lines:
    # Extract the orientation
    if '**cell' in line:
        orientation_num = int(TessFile_lines[TessFile_lines.index(line)+1])
    elif '*ori' in line:
        orientations = TessFile_lines[TessFile_lines.index(line)+2:TessFile_lines.index(line)+2+orientation_num]
        orientations_coord = extract_orientation(orientation_num, orientations)
        # print(orientations_coord)
    # ****************************************************************** #
    #                         Extract the vertices                       #
    # ****************************************************************** #
    elif 'Point' in line:
        # Extract the number of point from the line
        # e.g. Point(1)={161.186,369.387,0,e_def}; -> 1
        line_split = line.split('(')[1].split(')')
        Point_num = int(line_split[0])
        # Find the maximum number of point
        if Point_num > Vertex_mum_max:
            Vertex_mum_max = Point_num
        # Extract the coordinates of the point
        # e.g. Point(1)={161.186,369.387,0,e_def}; -> 161.186,369.387,0
        line_coord = line_split[1].split('{')[1].split('}')[0].split(',')
        coord_x = float(line_coord[0])
        coord_y = float(line_coord[1])
        coord_z = float(line_coord[2])
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
    # ****************************************************************** #
    #                           Extract the edges                        #
    # ****************************************************************** #
    elif 'Line' in line:
        if 'Loop' in line:
            continue
        else:
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
        
    elif 'BSpline' in line:
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
        Splines_vertices[Edge_num-1] = Spline_vertices
        
# There are still many information of grains not be extracted from the .Geo file
# Include the 'Plane surface' and 'Line loop' information

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
myModel = mdb.models["Model-1"]
sketch_base = myModel.ConstrainedSketch(name='__profile__', sheetSize=500.0)
# Defining the vertices of the base shell, and offset from the polycrystalline region
#
# Point4 |<-----------------Length---------------->| Point3
#        -------------------------------------------------
#        |                                             | ^
#        |                                             | |
#        |                                             | |
#        |                           Medium            | |
#        |                     -----------------       | |
#        |                     |               |       | |
#        |    Point6           |               |       | |
#  Point5----------\           |               |       | |
#                   \Crack tip |Polycrystalline|       | |
#                   / Point7   |    region     |       | |
#  Point9----------/           |               |       | Width
#        |    Point8           |               |       | |
#        |  offset_x           |               |       | |
#        |<------------------->-----------------       | |
#        |                     ^                       | |
#        |                     |                       | |
#        |                     |offset_y               | |
#        |                     |                       | |
#        -------------------------------------------------
#     Point1                                    Point2
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
offset_x = PR_length*0.2
offset_y = PR_length*0.2
Length   = 1000
Width    = 1000
Crack_length = offset_x
Crack_width  = 10
# The length of the base shell must longer than the polycrystalline region
# and so must the width relative to the polycrystalline region
if Length < PR_length:
    # If the length is shorter than the polycrystalline region, then the length 
    # is set to be the length of polycrystalline region plus double offset
    Length = (PR_length) + 2*offset_x
    print('The length of the base shell is short and have been set to \
           be the length of polycrystalline region plus double offset')
if Width < PR_width:
    # If the width is shorter than the polycrystalline region, then the width
    # is set to be the width of polycrystalline region plus double offset
    Width = (PR_width) + 2*offset_y
    print('The width of the base shell is short and have been set to \
           be the width of polycrystalline region plus double offset')
Point_1 = [coord_x_min - offset_x                 ,coord_y_min - offset_y                ,0]
Point_2 = [Point_1[0] + Length                    ,Point_1[1]                            ,0]
Point_3 = [Point_2[0]                             ,Point_2[1] + Width                    ,0]
Point_4 = [Point_3[0] - Length                    ,Point_3[1]                            ,0]
Point_5 = [Point_4[0]                             ,Point_4[1] - (Width - Crack_width)/2  ,0]
Point_6 = [Point_5[0] + Crack_length-Crack_width  , Point_5[1]                           ,0]
Point_7 = [Point_6[0] + Crack_width               , Point_6[1] - Crack_width/2.0         ,0]
Point_8 = [Point_7[0] - Crack_width               , Point_7[1] - Crack_width/2.0         ,0]
Point_9 = [Point_8[0] - Crack_length+Crack_width  , Point_8[1]                           ,0]
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
mypart = myModel.Part(name='Part-1', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
mypart.BaseShell(sketch=sketch_base)

# ********************************************************************** #
#       Create the grain boundaries by partition the base shell          #
# ********************************************************************** #
# grain boundaries obtained above
# Create the grain boundraies based on the straight edge
# ********************************************************************** #
print('Create the grain boundaries by straight edges')
mypart = myModel.parts['Part-1']
Sketch_GB = myModel.ConstrainedSketch(name='__profile__', sheetSize=500.0, gridSpacing=10)
Sketch_GB.setPrimaryObject(option=SUPERIMPOSE)
mypart.projectReferencesOntoSketch(sketch=Sketch_GB, filter=COPLANAR_EDGES)
# Loop over the straight edges
for Edge in Edges_vertices:
    if len(Edge) == 0:
        continue
    else:
        try:
            # Get the coordinates of the two vertices of the edge
            vertex_coord_1_x = vertex_coord[Edge[0]-1][0]
            vertex_coord_1_y = vertex_coord[Edge[0]-1][1]
            vertex_coord_2_x = vertex_coord[Edge[1]-1][0]
            vertex_coord_2_y = vertex_coord[Edge[1]-1][1]
            # Create the sketch of the grain boundary by straight edge
            Sketch_GB.Line(point1=(vertex_coord_1_x,vertex_coord_1_y), point2=(vertex_coord_2_x,vertex_coord_2_y))
        except:
            print(Edge)
            continue
# ********************************************************************** #
# Create the grain boundraies based on the curved edge
# ********************************************************************** #
print('Create the grain boundraies based on the curved edge')
iter = 0
# Loop over the curved edges
for Spline_vertices in Splines_vertices:
    if len(Spline_vertices) == 0:
        continue
    else:
        points_x = []
        points_y = []
        # Loop over the vertices of the spline
        for Spline_vertex in Spline_vertices:
            # Get the coordinates of the vertex and append to the string
            Spline_vertex_x = vertex_coord[Spline_vertex-1][0]
            Spline_vertex_y = vertex_coord[Spline_vertex-1][1]
            points_x.append(Spline_vertex_x)
            points_y.append(Spline_vertex_y)
        try:
            Sketch_GB.Spline(points=zip(points_x,points_y))
            iter = iter + 1
            # if iter > 500:
            #     break
        except:
            print(Spline_vertices)
            print(points_x)
            print(points_y)

f = mypart.faces
pickedFaces = f.getSequenceFromMask(mask=('[#1 ]', ), )
e1, d2 = mypart.edges, mypart.datums
mypart.PartitionFaceBySketch(faces=pickedFaces, sketch=Sketch_GB)
Sketch_GB.unsetPrimaryObject()

session.viewports['Viewport: 1'].setValues(displayedObject=mypart)
del myModel.sketches['__profile__']
# ********************************************************************** #