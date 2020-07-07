"""Map Generation World File Creator 
   Written by Fatemeh Pahlevan Aghababa and Amirreza Kabiri based on the code written by Robbie Goldman and Alfred Roberts
"""

import time
import os
import platform
try:
    import vrep
except:
    print('--------------------------------------------------------------')
    print('"vrep.py" could not be imported. This means very probably that')
    print('either "vrep.py" or the remoteApi library could not be found.')
    print('Make sure both are in the same folder as this file,')
    print('or appropriately adjust the file "vrep.py"')
    print('--------------------------------------------------------------')
    print('')

def linux_distribution():
  try:
    return platform.linux_distribution()
  except:
    return "N/A"

os_type='mac'
is_32=False
if platform.system() =='cli':
        os_type = 'windows'
elif platform.system() =='Windows':
        os_type = 'windows'
elif platform.system() == 'Darwin':
        os_type = 'mac'
elif platform.system() == 'Linux':
    if linux_distribution() == "N/A" :
      os_type = 'ubuntu_18'
    elif linux_distribution()[1] == '16.04':
        os_type = 'ubuntu_16'
    else:
        os_type = 'ubuntu_18'
else:
       os_type = 'windows' 
       is_32=True 

def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


base_path=resource_path("")
if os_type == 'mac':
  base_path=base_path.replace('Simplus.app/Contents/MacOS/','')

address=base_path.split('/')
if len(address)<2:
  address=base_path.split('\\')

postfix=len(address[-2])+1
base_path = base_path[:-1*postfix]
model_path =base_path +'generator'


vrep.simxFinish(-1)  # just in case, close all opened connections
clientID = vrep.simxStart('127.0.0.1', 12345, True, True,5000, 5)  # Connect to V-REP
print("client id", clientID)
try:
    returnCode,handler = vrep.simxGetObjectHandle(clientID=clientID,objectName="ResizableFloor_5_25",operationMode= vrep.simx_opmode_blocking)
    vrep.simxRemoveModel(clientID=clientID,objectHandle=handler,operationMode=vrep.simx_opmode_oneshot)
except:
     print("Can not remove the ResizableFloor_5_25")


from decimal import Decimal
import os
dirname = os.path.dirname(__file__)

def checkForCorners(pos, walls):
    '''Check if each of the corners is needed'''
    #Surrounding tile directions
    around = [[0, -1], [1, 0], [0, 1], [-1, 0]]
    #Needed corners
    corners = [False, False, False, False]

    surroundingTiles = []

    thisWall = walls[pos[1]][pos[0]]

    if not thisWall[0]:
        return corners

    #For each surrounding card
    for a in around:
        #Get the position
        xPos = pos[0] + a[0]
        yPos = pos[1] + a[1]
        #If it is a valid position
        if xPos > -1 and xPos < len(walls[0]) and yPos > -1 and yPos < len(walls):
            #Add the tile to the surrounding list
            surroundingTiles.append(walls[yPos][xPos])
        else:
            #Otherwise add a null value
            surroundingTiles.append([False, [False, False, False, False], False, False, False])

    #If top right is needed
    corners[0] = surroundingTiles[0][1][1] and surroundingTiles[1][1][0] and not thisWall[1][0] and not thisWall[1][1]
    #If bottom right is needed
    corners[1] = surroundingTiles[1][1][2] and surroundingTiles[2][1][1] and not thisWall[1][1] and not thisWall[1][2]
    #If bottom left is needed
    corners[2] = surroundingTiles[2][1][3] and surroundingTiles[3][1][2] and not thisWall[1][2] and not thisWall[1][3]
    #If top left is needed
    corners[3] = surroundingTiles[0][1][3] and surroundingTiles[3][1][0] and not thisWall[1][3] and not thisWall[1][0]

    return corners


def checkForExternalWalls (pos, walls):
    '''Convert tile position to a list of bools for needed external walls'''
    #Get the tile at the position
    thisWall = walls[pos[1]][pos[0]]

    #If there is no tile here there is no need for an external wall
    if not thisWall[0]:
        return [False, False, False, False]

    #Surrounding tiles
    around = [[0, -1], [1, 0], [0, 1], [-1, 0]]
    otherTiles = [False, False, False, False]

    d = 0
    
    for a in around:
        #Get the tiles position
        xPos = pos[0] + a[0]
        yPos = pos[1] + a[1]
        #If it is a valid positon
        if xPos > -1 and xPos < len(walls[0]) and yPos > -1 and yPos < len(walls):
            #Add the tiles present data
            otherTiles[d] = walls[yPos][xPos][0]
        else:
            #No tile present
            otherTiles[d] = False
        #Add one to direction counter
        d = d + 1

    #Convert to needed walls
    externalsNeeded = [not otherTiles[0], not otherTiles[1], not otherTiles[2], not otherTiles[3]]
    return externalsNeeded


def checkForNotch (pos, walls):
    '''Determine if a notch is needed on either side'''
    #Variables to store if each notch is needed
    needLeft = False
    needRight = False

    #No notches needed if there is not a floor
    if not walls[pos[1]][pos[0]][0]:
        return False, False, 0

    rotations = [3.14159, 1.57079, 0, -1.57079]

    #Surrounding tiles
    around = [[0, -1], [1, 0], [0, 1], [-1, 0]]
    #Tiles to check if notches are needed
    notchAround = [[ [1, -1], [-1, -1] ],
                   [ [1, 1], [1, -1] ],
                   [ [-1, 1], [1, 1] ],
                   [ [-1, -1], [-1, 1] ]]

    #Current direction
    d = 0
    #Number of surrounding tiles
    surround = 0

    #Direction of present tile
    dire = -1

    #Iterate for surrounding tiles
    for a in around:
        #If x axis is within array
        if pos[0] + a[0] < len(walls[0]) and pos[0] + a[0] > -1:
            #If y axis is within array
            if pos[1] + a[1] < len(walls) and pos[1] + a[1] > -1:
                #If there is a tile there
                if walls[pos[1] + a[1]][pos[0] + a[0]][0]:
                    #Add to number of surrounding tiles
                    surround = surround + 1
                    #Store direction
                    dire = d
        #Increment direction
        d = d + 1

    rotation = 0

    #If there was only one connected tile and there is a valid stored direction
    if surround == 1 and dire > -1 and dire < len(notchAround):
        #Get the left and right tile positions to check
        targetLeft = [pos[0] + notchAround[dire][0][0], pos[1] + notchAround[dire][0][1]]
        targetRight = [pos[0] + notchAround[dire][1][0], pos[1] + notchAround[dire][1][1]]

        #If the left tile is a valid target position
        if targetLeft[0] < len(walls[0]) and targetLeft[0] > -1 and targetLeft[1] < len(walls) and targetLeft[1] > -1:
            #If there is no tile there
            if not walls[targetLeft[1]][targetLeft[0]][0]:
                #A left notch is needed
                needLeft = True

        #If the right tile is a valid target position
        if targetRight[0] < len(walls[0]) and targetRight[0] > -1 and targetRight[1] < len(walls) and targetRight[1] > -1:
            #If there is no tile there
            if not walls[targetRight[1]][targetRight[0]][0]:
                #A right notch is needed
                needRight = True

        rotation = rotations[dire]

    #Return information about needed notches
    return needLeft, needRight, rotation


def makeFile(walls, obstacles, thermal, visual, startPos, uiWindow = None):
    '''Create a file data string from the positions and scales'''
   
    #Strings to hold the tile parts
    allTiles = ""
    #Strings to hold the boundaries for special tiles
    allCheckpointBounds = ""
    allTrapBounds = ""
    allGoalBounds = ""
    allSwampBounds = ""

    #Upper left corner to start placing tiles from
    width = len(walls[0])
    height = len(walls)
    startX = -(len(walls[0]) * 0.25 / 2.0)
    startZ = -(len(walls) * 0.25 / 2.0)

    #Id numbers used to give a unique but interable name to tile pieces
    tileId = 0
    checkId = 0
    trapId = 0
    goalId = 0
    swampId = 0

    #Iterate through all the tiles
    for x in range(0, len(walls[0])):
        for z in range(0, len(walls)):
            #Check which corners and external walls and notches are needed
            corners = checkForCorners([x, z], walls)
            externals = checkForExternalWalls([x, z], walls)
            notchData = checkForNotch([x, z], walls)
            notch = ""
            #Set notch string to correct value
            if notchData[0]:
                notch = "left"
            if notchData[1]:
                notch = "right"
            
            #tile
            # print( "V-REP add tile")
            isTile=False

            #wall 
            if walls[z][x][1][0]: #top
                # print( "V-REP add top wall")
                resetCode, obj = vrep.simxLoadModel(clientID=clientID,modelPathAndName=model_path+'/models/walls/top_wall.ttm',options=0,operationMode=vrep.simx_opmode_blocking)
                returnCode,position = vrep.simxGetObjectPosition(clientID=clientID,objectHandle = obj, relativeToObjectHandle = -1, operationMode=vrep.simx_opmode_blocking)
                pos_z = position[2]
                vrep.simxSetObjectPosition(clientID=clientID,objectHandle=obj,relativeToObjectHandle=-1,position=( (x * 0.25 + startX),-1*(z * 0.25 + startZ)+0.125 ,pos_z),operationMode=vrep.simx_opmode_oneshot)
                
            if walls[z][x][1][1]: #right
                # print( "V-REP add right wall")
                resetCode, obj = vrep.simxLoadModel(clientID=clientID,modelPathAndName=model_path+'/models/walls/right_wall.ttm',options=0,operationMode=vrep.simx_opmode_blocking)
                returnCode,position = vrep.simxGetObjectPosition(clientID=clientID,objectHandle = obj, relativeToObjectHandle = -1, operationMode=vrep.simx_opmode_blocking)
                pos_z = position[2]
                vrep.simxSetObjectPosition(clientID=clientID,objectHandle=obj,relativeToObjectHandle=-1,position=( (x * 0.25 + startX)+0.25,-1*(z * 0.25 + startZ)+0.125 ,pos_z),operationMode=vrep.simx_opmode_oneshot)
                
            if  walls[z][x][1][2]: #bottom
                # print( "V-REP add bottom wall")
                resetCode, obj = vrep.simxLoadModel(clientID=clientID,modelPathAndName=model_path+'/models/walls/bottom_wall.ttm',options=0,operationMode=vrep.simx_opmode_blocking)
                returnCode,position = vrep.simxGetObjectPosition(clientID=clientID,objectHandle = obj, relativeToObjectHandle = -1, operationMode=vrep.simx_opmode_blocking)
                pos_z = position[2]
                vrep.simxSetObjectPosition(clientID=clientID,objectHandle=obj,relativeToObjectHandle=-1,position=( (x * 0.25 + startX)+0.125,-1*(z * 0.25 + startZ)-0.25 ,pos_z),operationMode=vrep.simx_opmode_oneshot)
                
            if walls[z][x][1][3]: #left
                # print( "V-REP add left wall")
                resetCode, obj = vrep.simxLoadModel(clientID=clientID,modelPathAndName=model_path+'/models/walls/left_wall.ttm',options=0,operationMode=vrep.simx_opmode_blocking)
                returnCode,position = vrep.simxGetObjectPosition(clientID=clientID,objectHandle = obj, relativeToObjectHandle = -1, operationMode=vrep.simx_opmode_blocking)
                pos_z = position[2]
                vrep.simxSetObjectPosition(clientID=clientID,objectHandle=obj,relativeToObjectHandle=-1,position=( (x * 0.25 + startX),-1*(z * 0.25 + startZ)+0.125 ,pos_z),operationMode=vrep.simx_opmode_oneshot)
                

            #checkpoint
            if walls[z][x][2]:
                #Add bounds to the checkpoint boundaries
                print( "V-REP add checkpoint")
                resetCode, obj = vrep.simxLoadModel(clientID=clientID,modelPathAndName=model_path+'/models/tiles/checkpoint_tile.ttm',options=0,operationMode=vrep.simx_opmode_blocking)
                returnCode,position = vrep.simxGetObjectPosition(clientID=clientID,objectHandle = obj, relativeToObjectHandle = -1, operationMode=vrep.simx_opmode_blocking)
                pos_z = position[2]
                vrep.simxSetObjectPosition(clientID=clientID,objectHandle=obj,relativeToObjectHandle=-1,position=( (x * 0.25 + startX),-1*(z * 0.25 + startZ) ,pos_z),operationMode=vrep.simx_opmode_oneshot)
                # allCheckpointBounds = allCheckpointBounds + boundsPart.format("checkpoint", checkId, (x * 0.25 + startX) - 0.15, (z * 0.25 + startZ) - 0.15, (x * 0.25 + startX) + 0.15, (z * 0.25 + startZ) + 0.15)
                #Increment id counter
                checkId = checkId + 1
                isTile=True
                    
            #trap
            if walls[z][x][3]:
                #Add bounds to the trap boundaries
                print( "V-REP add trap / hole tile")
                resetCode, obj = vrep.simxLoadModel(clientID=clientID,modelPathAndName=model_path+'/models/tiles/hole_tile.ttm',options=0,operationMode=vrep.simx_opmode_blocking)
                returnCode,position = vrep.simxGetObjectPosition(clientID=clientID,objectHandle = obj, relativeToObjectHandle = -1, operationMode=vrep.simx_opmode_blocking)
                pos_z = position[2]
                vrep.simxSetObjectPosition(clientID=clientID,objectHandle=obj,relativeToObjectHandle=-1,position=( (x * 0.25 + startX),-1*(z * 0.25 + startZ) ,pos_z),operationMode=vrep.simx_opmode_oneshot)
          
                # allTrapBounds = allTrapBounds + boundsPart.format("trap", trapId, (x * 0.25 + startX) - 0.15, (z * 0.25 + startZ) - 0.15, (x * 0.25 + startX) + 0.15, (z * 0.25 + startZ) + 0.15)
                #Increment id counter
                trapId = trapId + 1
                isTile = True
                    
            #goal
            if walls[z][x][4]:
                #Add bounds to the goal boundaries
                print( "V-REP add start tile")
                resetCode, obj = vrep.simxLoadModel(clientID=clientID,modelPathAndName=model_path+'/models/tiles/start_tile.ttm',options=0,operationMode=vrep.simx_opmode_blocking)
                returnCode,position = vrep.simxGetObjectPosition(clientID=clientID,objectHandle = obj, relativeToObjectHandle = -1, operationMode=vrep.simx_opmode_blocking)
                pos_z = position[2]
                vrep.simxSetObjectPosition(clientID=clientID,objectHandle=obj,relativeToObjectHandle=-1,position=( (x * 0.25 + startX),-1*(z * 0.25 + startZ) ,pos_z),operationMode=vrep.simx_opmode_oneshot)
          
                resetCode, obj_robot = vrep.simxLoadModel(clientID=clientID,modelPathAndName=model_path+'/models/robots/simplus_e-puck.ttm',options=0,operationMode=vrep.simx_opmode_blocking)
                returnCode,position = vrep.simxGetObjectPosition(clientID=clientID,objectHandle = obj_robot, relativeToObjectHandle = -1, operationMode=vrep.simx_opmode_blocking)
                pos_z = position[2]
                print("V-rep add robot")
                vrep.simxSetObjectPosition(clientID=clientID,objectHandle=obj_robot,relativeToObjectHandle=-1,position=( (x * 0.25 + startX),-1*(z * 0.25 + startZ) ,pos_z),operationMode=vrep.simx_opmode_oneshot)
                 
                resetCode, obj = vrep.simxLoadModel(clientID=clientID,modelPathAndName=model_path+'/models/game_manager.ttm',options=0,operationMode=vrep.simx_opmode_blocking)
                returnCode,position = vrep.simxGetObjectPosition(clientID=clientID,objectHandle = obj, relativeToObjectHandle = -1, operationMode=vrep.simx_opmode_blocking)
                vrep.simxSetObjectPosition(clientID=clientID,objectHandle=obj,relativeToObjectHandle=-1,position=(20,20,0),operationMode=vrep.simx_opmode_oneshot)

                #Increment id counter
                goalId = goalId + 1
                isTile = True
            #swamp
            if walls[z][x][5]:
                print( "V-REP add swamp tile")
                resetCode, obj = vrep.simxLoadModel(clientID=clientID,modelPathAndName=model_path+'/models/tiles/speed_bump.ttm',options=0,operationMode=vrep.simx_opmode_blocking)
                returnCode,position = vrep.simxGetObjectPosition(clientID=clientID,objectHandle = obj, relativeToObjectHandle = -1, operationMode=vrep.simx_opmode_blocking)
                pos_z = position[2]
                vrep.simxSetObjectPosition(clientID=clientID,objectHandle=obj,relativeToObjectHandle=-1,position=( (x * 0.25 + startX),-1*(z * 0.25 + startZ) ,pos_z),operationMode=vrep.simx_opmode_oneshot)
          
                #Add bounds to the swamp boundaries
                # allSwampBounds = allSwampBounds + boundsPart.format("swamp", swampId, (x * 0.25 + startX) - 0.15, (z * 0.25 + startZ) - 0.15, (x * 0.25 + startX) + 0.15, (z * 0.25 + startZ) + 0.15)
                #Increment id counter
                swampId = swampId + 1
                isTile = True
            # white tile
            if not isTile:
                resetCode, obj = vrep.simxLoadModel(clientID=clientID,modelPathAndName=model_path+'/models/tiles/tile_white.ttm',options=0,operationMode=vrep.simx_opmode_blocking)
                returnCode,position = vrep.simxGetObjectPosition(clientID=clientID,objectHandle = obj, relativeToObjectHandle = -1, operationMode=vrep.simx_opmode_blocking)
                pos_z = position[2]
                vrep.simxSetObjectPosition(clientID=clientID,objectHandle=obj,relativeToObjectHandle=-1,position=( (x * 0.25 + startX),-1*(z * 0.25 + startZ) ,pos_z),operationMode=vrep.simx_opmode_oneshot)
                
            #Increment id counter
            tileId = tileId + 1




    #String to hold all the data for the obstacles
    allObstacles = ""
    allDebris = ""

    #Id to give a unique name to the obstacles
    obstacleId = 0
    debrisId = 0

    #Iterate obstalces
    for obstacle in obstacles:
        #If this is debris
        if obstacle[3]:
            #Add the debris object
            # allDebris = allDebris + debrisPart.format(debrisId, obstacle[0], obstacle[1], obstacle[2])
            #Increment id counter
            debrisId = debrisId + 1
        else:
            #Add the obstacle
            # allObstacles = allObstacles + obstaclePart.format(obstacleId, obstacle[0], obstacle[1], obstacle[2])
            #Increment id counter
            obstacleId = obstacleId + 1

    
    #Return the file data as a string
    return 



