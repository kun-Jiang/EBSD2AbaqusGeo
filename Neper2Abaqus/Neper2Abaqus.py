# -*- coding: mbcs -*-
# Do not delete the following import lines
from abaqus import *
from abaqusConstants import *
import __main__
import os
import numpy as np

def logwrite(word):
    logfile = open('log.txt','a')
    logfile.write(word)
    print(word)
    logfile.close()


def extract_orientation(orientation_num, orientations):
    # iterate over the list of strings
    phi1 = []
    phi2 = []
    phi3 = []
    with open('orientations.txt', 'w') as f:
        f.write('phi1\tphi2\tphi3\n')
        for orientation in orientations:
            # split each string at the space character
            orientation_split = orientation.split(' ')
            # remove empty strings and the '0' at the end of each line
            orientation_split = list(filter(lambda x: x != '' and x != '0\n', orientation_split))
            # convert strings to floats
            phi1.append(float(orientation_split[0]))
            phi2.append(float(orientation_split[1]))
            phi3.append(float(orientation_split[2]))
            f.write( str(float(orientation_split[0]))+'\t'
                    +str(float(orientation_split[1]))+'\t'
                    +str(float(orientation_split[2]))+'\n')
    return phi1, phi2, phi3

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

def extract_faces(face_num, faces):
    
    grain_edges_list = []
    # Loop over the faces
    for i in range(face_num):
        faces_index = []
        line = str(faces[i*4+1])
        # Split the face into edge indices
        face_edge_split = str(line).split(' ')
        # Remove empty string
        face_edge_split = list(filter(lambda x: x != '', face_edge_split))
        # Remove the first and second string: the first string is the face index, the second string is the number of edges
        face_edge_split.remove(face_edge_split[0])
        for face_edge in face_edge_split:
            # Remove the newline character
            if '\n' in face_edge:
                face_edge = face_edge.split('\n')[0]
            # Save the edge index
            faces_index.append(int(face_edge))
        # Save the edges of each grain
        grain_edges_list.append(faces_index)
    
    return grain_edges_list
        
def find_center(face_vertices, vertex_coord, i):
    # Calculating the centroid of polygon (https://www.zhihu.com/question/337823261)
    # Shoelace Theorem to calculate the area of the polygon (https://zhuanlan.zhihu.com/p/110025234)
    area_sum = 0
    term_x_sum = 0
    term_y_sum = 0
    for i in range(len(face_vertices)):
        coord_x_i = vertex_coord[face_vertices[i]-1][0]
        coord_y_i = vertex_coord[face_vertices[i]-1][1]
        if i+1 > len(face_vertices)-1:
            coord_x_i_1 = vertex_coord[face_vertices[0]-1][0]
            coord_y_i_1 = vertex_coord[face_vertices[0]-1][1]
        else:
            coord_x_i_1 = vertex_coord[face_vertices[i+1]-1][0]
            coord_y_i_1 = vertex_coord[face_vertices[i+1]-1][1]
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


#get current working directory
WorkingDirectory = os.getcwd()
#change current working directory to current working directory
os.chdir(WorkingDirectory)
# **********************************************************************
#                        Inputing the .tess file name
# **********************************************************************
# Open the file
# TessFile_Name  = "test"
# crack_width = 0.01
# crack_length = 0.2
TessFile_list       = os.listdir(WorkingDirectory)
TessFile = [i for i in TessFile_list if i.endswith('.tess')]

with open(TessFile[0], 'r') as f:

# TessFile       = open("%s.tess"%TessFile_Name,'r')
    TessFile_lines = f.readlines()
# TessFile.close()
# **********************************************************************
#       Extract the orientation, vertices and edges information
# **********************************************************************
grain_edges_list = []
for line in TessFile_lines:
    # Extract the orientation
    if '**cell' in line:
        orientation_num = int(TessFile_lines[TessFile_lines.index(line)+1])
    elif '*ori' in line:
        orientations = TessFile_lines[TessFile_lines.index(line)+2:TessFile_lines.index(line)+2+orientation_num]
        [phi1, phi2, phi3] = extract_orientation(orientation_num, orientations)
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
    # Extract the faces
    elif '**face' in line:
        face_num = int(TessFile_lines[TessFile_lines.index(line)+1])
        faces = TessFile_lines[TessFile_lines.index(line)+2:TessFile_lines.index(line)+2+face_num*4]
        grain_edges_list = extract_faces(face_num, faces)
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
Point_1 = [coord_min[0],coord_min[1]]
Point_2 = [coord_max[0],coord_min[1]]
Point_3 = [coord_max[0],coord_max[1]]
Point_4 = [coord_min[0],coord_max[1]]
myModel = mdb.models["Model-1"]
sketch1 = myModel.ConstrainedSketch(name='__profile__', sheetSize=200.0)
# Create the marginal edge Y0  node1 -> node2
sketch1.Line(point1=(coord_min[0],coord_min[1]), point2=(coord_max[1],coord_min[0]))
# Create the marginal edge X1  node2 -> node3
sketch1.Line(point1=(coord_max[1],coord_min[0]), point2=(coord_max[0],coord_max[1]))
# Create the marginal edge Y1  node3 -> node4
sketch1.Line(point1=(coord_max[0],coord_max[1]), point2=(coord_min[0],coord_max[1]))
# Create the marginal edge X0  node4 -> node1
X0_length = coord_max[1] - coord_min[1]
sketch1.Line(point1=(coord_min[0],coord_max[1]), point2=(coord_min[0],coord_min[1]))


mypart = myModel.Part(name='Part-1', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
mypart.BaseShell(sketch=sketch1)

# ********************************************************************** #
#       Create the grain boundaries by partition the base shell          #
#                    grain boundaries obtained above
# ********************************************************************** #
# Create the grain boundaries by partition the base shell
print('Creating grains')
mypart = myModel.parts['Part-1']
Sketch_GB = myModel.ConstrainedSketch(name='__profile__', sheetSize=500.0, gridSpacing=10)
Sketch_GB.setPrimaryObject(option=SUPERIMPOSE)
mypart.projectReferencesOntoSketch(sketch=Sketch_GB, filter=COPLANAR_EDGES)
center_all = [[]]*face_num
for i in range(face_num):
    grain_edges = grain_edges_list[i]
    face_vertices = []
    try:
        # If there have exist the same material, skip the process
        material_name = 'Mat_' + str(i+1)
        mdb.models['Model-1'].Material(name=material_name)
        mdb.models['Model-1'].materials[material_name].UserMaterial(
        mechanicalConstants=(10000000000.0, 0.33, i+1))
    except:
        pass
    for edge_num in grain_edges:
        edge_num = abs(edge_num)
        vertices = edges_vertex[edge_num-1]
        vertex_1 = vertices[0]
        vertex_2 = vertices[1]
        face_vertices.append(vertices[0])
        face_vertices.append(vertices[1])
        if edge_num in interior_edges:

            vertex_coord_1_x = vertex_coord[vertex_1-1][0]
            vertex_coord_1_y = vertex_coord[vertex_1-1][1]
            vertex_coord_2_x = vertex_coord[vertex_2-1][0]
            vertex_coord_2_y = vertex_coord[vertex_2-1][1]

            try:
                # Create the sketch of the grain boundary by straight edge
                Sketch_GB.Line(point1=(vertex_coord_1_x,vertex_coord_1_y), point2=(vertex_coord_2_x,vertex_coord_2_y))
                # Remove the line number that has been used
                # grain_edges_list.remove(abs(edge_num))
                # print(abs(edge_num))
                interior_edges.remove(edge_num)
            except:
                print('There is something wrong when creating the sketch by straight edge')
                print(vertices)
    
    face_vertices = list(set(face_vertices[:4]))
    center = find_center(face_vertices, vertex_coord, i)
    center_all[i] = [center[0], center[1]]

    f = mypart.faces
    # Find the base face based on the point_1 mentioned above
    base_face = f.findAt(((center[0], center[1], 0), ) )
    
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
    

    
    milestone('Creating curved edge',i+1/face_num)

if Local_sys_exist == 1:
    mdb.models['Model-1'].parts['Part-1'].MaterialOrientation(region=region_homo, 
        orientationType=GLOBAL, axis=AXIS_3, 
        additionalRotationType=ROTATION_NONE, localCsys=None, fieldName='', 
        stackDirection=STACK_3)
logwrite('{0:-^68}'.format('Finished successfully') + '\n')
del myModel.sketches['__profile__']


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