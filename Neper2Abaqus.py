# -*- coding: mbcs -*-
# Do not delete the following import lines
from abaqus import *
from abaqusConstants import *
import __main__
import os

def extract_orientation(orientation_num, orientations):
    # iterate over the list of strings
    orientations_coord = []
    for orientation in orientations:
        # split each string at the space character
        orientation_split = orientation.split(' ')
        # remove empty strings and the '0' at the end of each line
        orientation_split = list(filter(lambda x: x != '' and x != '0\n', orientation_split))
        # convert strings to floats
        orientations_coord.append([float(orientation_split[0]), float(orientation_split[1]), float(orientation_split[2])])
    return orientations_coord

# define the function extract_vertex, it takes a list of strings as input
def extract_vertex(vertex_num, vertices):
    # iterate over the list of strings
    vertices_coord = []
    coord_min = [0,0]
    coord_max = [0,0]
    for vertex in vertices:
        # split each string at the space character
        vertex_split = vertex.split(' ')
        # remove empty strings and the '0' at the end of each line
        vertex_split = list(filter(lambda x: x != '' and x != '0\n', vertex_split))
        # convert strings to floats
        vertices_coord.append([float(vertex_split[1]), float(vertex_split[2]), float(vertex_split[3])])
        if float(vertex_split[1]) < coord_min[0]:
            coord_min[0] = float(vertex_split[1])
        elif float(vertex_split[1]) > coord_max[0]:
            coord_max[0] = float(vertex_split[1])
        elif float(vertex_split[2]) < coord_min[1]:
            coord_min[1] = float(vertex_split[2])
        elif float(vertex_split[2]) > coord_max[1]:
            coord_max[1] = float(vertex_split[2])
            
            
    return vertices_coord,coord_min,coord_max

def extract_edges(edge_num, edges):
    # iterate over the list of strings
    edges_vertex = []
    edges_index = []
    for edge in edges:
        # split each string at the space character
        edge_split = edge.split(' ')
        # remove empty strings and the '0' at the end of each line
        edge_split = list(filter(lambda x: x != '' and x != '0\n', edge_split))
        # convert strings to floats
        edges_index.append(int(edge_split[0]))
        edges_vertex.append([int(edge_split[1]), int(edge_split[2])])
    edges_index = set(edges_index)
    return edges_vertex,edges_index

def extract_marginal_edges(marginal_edge_num, marginal_edges):
    marginal_edges_index = []
    # Loop over the marginal edges
    for i in range(marginal_edge_num):
        line = str(marginal_edges[i*3+2])
        # Split the marginal edge into edge indices
        marginal_edges_split = str(line).split(' ')
        # Remove empty string
        marginal_edges_split = list(filter(lambda x: x != '', marginal_edges_split))
        # Remove first string
        marginal_edges_split.remove(marginal_edges_split[0])
        # Loop over the edge indices
        for marginal_edge in marginal_edges_split:
            # Remove the newline character
            if '\n' in marginal_edge:
                marginal_edge = marginal_edge.split('\n')[0]
            # Save the edge index
            marginal_edges_index.append(int(marginal_edge))
    # Remove duplicate edge indices
    marginal_edges_index = set(marginal_edges_index)
    
    return marginal_edges_index
        


#get current working directory
WorkingDirectory = os.getcwd()
#change current working directory to current working directory
os.chdir(WorkingDirectory)
# **********************************************************************
#                        Inputing the .tess file name
# **********************************************************************
# Open the file
TessFile_Name  = "test1"
crack_width = 0.01
crack_length = 0.2
TessFile       = open("%s.tess"%TessFile_Name,'r')
TessFile_lines = TessFile.readlines()
TessFile.close()
# **********************************************************************
#       Extract the orientation, vertices and edges information
# **********************************************************************
for line in TessFile_lines:
    # Extract the orientation
    if '**cell' in line:
        orientation_num = int(TessFile_lines[TessFile_lines.index(line)+1])
    elif '*ori' in line:
        orientations = TessFile_lines[TessFile_lines.index(line)+2:TessFile_lines.index(line)+2+orientation_num]
        orientations_coord = extract_orientation(orientation_num, orientations)
        # print(orientations_coord)
    # Extract the nodes
    elif '**vertex' in line:
        vertex_num = int(TessFile_lines[TessFile_lines.index(line)+1])
        vertices = TessFile_lines[TessFile_lines.index(line)+2:TessFile_lines.index(line)+2+vertex_num]
        vertex_coord,coord_min,coord_max = extract_vertex(vertex_num, vertices)
        # print(vertex_coord)
    # Extract the edges
    elif '**edge' in line:
        edge_num = int(TessFile_lines[TessFile_lines.index(line)+1])
        edges = TessFile_lines[TessFile_lines.index(line)+2:TessFile_lines.index(line)+2+edge_num]
        edges_vertex,edges_index = extract_edges(edge_num, edges)
        # print(edges_vertex)
    # Extract the marginal edges
    elif '*edge' in line:
        marginal_edges_num = int(TessFile_lines[TessFile_lines.index(line)+1])
        marginal_edges = TessFile_lines[TessFile_lines.index(line)+2:TessFile_lines.index(line)+2+marginal_edges_num*3]
        marginal_edges_index = extract_marginal_edges(marginal_edges_num, marginal_edges)
        # print(marginal_edges_index)
interior_edges = edges_index - marginal_edges_index
# print(interior_edges)

# # Create the sketch of marginal edges
# myModel = mdb.models["Model-1"]
# sketch1 = myModel.ConstrainedSketch(name='__profile__', sheetSize=200.0)
# for marginal_edge in marginal_edges_index:
#     edge = edges_vertex[marginal_edge-1]
#     vertex_coord_1_x = vertex_coord[edge[0]-1][0]
#     vertex_coord_1_y = vertex_coord[edge[0]-1][1]
#     vertex_coord_2_x = vertex_coord[edge[1]-1][0]
#     vertex_coord_2_y = vertex_coord[edge[1]-1][1]
#     # Create the base shell
#     sketch1.Line(point1=(vertex_coord_1_x,vertex_coord_1_y), point2=(vertex_coord_2_x,vertex_coord_2_y))
    
# mypart = myModel.Part(name='Part-1', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
# mypart.BaseShell(sketch=sketch1)

# *********************************************************
# Create the sketch of marginal retangle and crack tip
# The sketch is implemented according following diagram
#          4                                     3
#           -------------------------------------
#           |                                   |
#           |                                   |
#           |                                   |
#           |                                   |
#         5 -----------------6                  |
#                           |                   |
#          8-----------------7                  |
#           |                                   |
#           |                                   |
#           |                                   |
#           |                                   |
#           -------------------------------------
#          1                                     2
#
#
myModel = mdb.models["Model-1"]
sketch1 = myModel.ConstrainedSketch(name='__profile__', sheetSize=200.0)
# Create the marginal edge Y0  node1 -> node2
sketch1.Line(point1=(coord_min[0],coord_min[1]), point2=(coord_max[1],coord_min[0]))
# Create the marginal edge X1  node2 -> node3
sketch1.Line(point1=(coord_max[1],coord_min[0]), point2=(coord_max[0],coord_max[1]))
# Create the marginal edge Y1  node3 -> node4
sketch1.Line(point1=(coord_max[0],coord_max[1]), point2=(coord_min[0],coord_max[1]))
# Create the marginal edge X0 upper the crack  node4 -> node5
# length of the edge X0
X0_length = coord_max[1] - coord_min[1]
sketch1.Line(point1=(coord_min[0],coord_max[1]), point2=(coord_min[0],(X0_length + crack_width)/2.0))
# Create the marginal edge X0 underneath the crack  node1 -> node8
sketch1.Line(point1=(coord_min[0],coord_min[1]), point2=(coord_min[0],(X0_length - crack_width)/2.0))

# Create the depth of crack  
# node5 -> node6
sketch1.Line(point1=(coord_min[0],(X0_length + crack_width)/2.0), point2=(coord_min[0]+crack_length,(X0_length + crack_width)/2.0))
# node6 -> node7
sketch1.Line(point1=(coord_min[0]+crack_length,(X0_length + crack_width)/2.0), point2=(coord_min[0]+crack_length,(X0_length - crack_width)/2.0))
# node7 -> node8
sketch1.Line(point1=(coord_min[0]+crack_length,(X0_length - crack_width)/2.0), point2=(coord_min[0],(X0_length - crack_width)/2.0))
mypart = myModel.Part(name='Part-1', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
mypart.BaseShell(sketch=sketch1)

# *********************************************************

# *********************************************************
# Create the grain boundaries by partition the base shell
mypart = myModel.parts['Part-1']
Sketch2 = myModel.ConstrainedSketch(name='__profile__', sheetSize=200.0, gridSpacing=10)
Sketch2.setPrimaryObject(option=SUPERIMPOSE)
mypart = myModel.parts['Part-1']
mypart.projectReferencesOntoSketch(sketch=Sketch2, filter=COPLANAR_EDGES)
# grain boundaries obtained above
for interior_edge in interior_edges:
    edge = edges_vertex[interior_edge-1]
    # prescribe coordinates of two vertices of the edge
    vertex_coord_1_x = vertex_coord[edge[0]-1][0]
    vertex_coord_1_y = vertex_coord[edge[0]-1][1]
    vertex_coord_2_x = vertex_coord[edge[1]-1][0]
    vertex_coord_2_y = vertex_coord[edge[1]-1][1]
    # Create the partiton face
    Sketch2.Line(point1=(vertex_coord_1_x,vertex_coord_1_y), point2=(vertex_coord_2_x,vertex_coord_2_y))

f = mypart.faces
pickedFaces = f.getSequenceFromMask(mask=('[#1 ]', ), )
e1, d2 = mypart.edges, mypart.datums
mypart.PartitionFaceBySketch(faces=pickedFaces, sketch=Sketch2)
Sketch2.unsetPrimaryObject()
session.viewports['Viewport: 1'].setValues(displayedObject=mypart)
del myModel.sketches['__profile__']
