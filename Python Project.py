#################################################
# Name: Mengrou Shou
#################################################

from cmu_112_graphics import *
import random, time, math, copy

#################################################
# Initial Set-up
#################################################

def gameDimensions():
    rows = 10
    cols = 10
    cellSize = 60
    margin = 30
    leftMargin = cellSize + margin
    return (rows, cols, cellSize, margin, leftMargin)

def playSnL():
    rows, cols, cellSize, margin, leftMargin = gameDimensions()
    width = cols * cellSize + margin + leftMargin
    height = rows * cellSize + 2 * margin
    runApp(width=width, height=height)

def appStarted(app):
    app.rows, app.cols, app.cellSize, app.margin, app.leftMargin = gameDimensions()
    # Splash Screen
    app.instrWidth = app.width/10
    app.instrX1, app.instrY1 = app.width-app.margin/2, app.height-app.margin/2
    app.instrX0, app.instrY0 = app.instrX1 - app.instrWidth, app.instrY1 - app.instrWidth
    app.needInstructions = False
    app.hasStarted = False
    app.playerRow, app.playerCol = app.rows - 1, -1
    # Map Generation
    app.ladders = {}
    app.allSolutions = []
    if (app.rows % 2 == 0):
        app.winRow, app.winCol = 0, 0
    else:
        app.winRow, app.winCol = 0, app.cols - 1
    generateLadders(app)
    app.laddersCopy = copy.deepcopy(app.ladders)
    app.snakes = {}
    generateSnakes(app)
    app.snakesCopy = copy.deepcopy(app.snakes)
    app.win = False
    # Time Initialization
    app.isPaused = False
    app.startTime = time.time()
    app.timerCalls = 0
    app.timerDelay = 1
    # Initialize Fastest Path
    # enemy 1
    app.enemyRow, app.enemyCol = app.rows - 1, -1
    app.enemyAllPath = {}
    app.enemyUnvisited = set()
    initBestPath(app, app.enemyRow, app.enemyCol)
    app.enemyMode = False
    app.enemyStartTime = 0
    app.gameOver = False
    # enemy 2
    app.sabotageRow, app.sabotageCol = -1, -1
    app.sabotageAllPath = {}
    app.sabotageUnvisited = set()
    initBestPath(app, app.sabotageRow, app.sabotageCol)
    app.sabotageMode = False
    app.sabotageStartTime = 0
    app.finishSabo = True
    # Locked ladders
    longestLadderIndex = -1
    bestLength = 0
    for i in app.ladders:
        row0, col0, row1, col1 = app.ladders[i]
        ladderLength = math.sqrt((row1 - row0)**2 + (col1 - col0)**2)
        if ladderLength > bestLength:
            longestLadderIndex = i
            bestLength = ladderLength
    if bestLength != 0: # found longestLadder
        app.lockedLadderIndex = longestLadderIndex
        app.keyRow, app.keyCol = longestLadderIndex, 0
        app.hasKey = False
    # make ladders
    app.madeLadder = []
    app.buildLadder = False
    # score keeping
    app.points = 0
    app.visitedCells = set()

def initBestPath(app, currRow, currCol):
    app.adjacent = {}
    app.weight = {}
    populateAdjAndWt(app)
    app.enemyPath = []
    app.sabotagePath = []
    app.startingCell = (0, 0)

#################################################
# Find Fastest Path
#################################################

def populateAdjAndWt(app):
    for j in range(app.rows):
        app.adjacent[(j, -1)] = [(j, 0)]
        app.weight[(j, -1)] = [1]
    for row in range(app.rows):
        for col in range(app.cols):
            if col == 0: # left edge cell
                if ((row - (app.rows - 1)) % 2 == 1):
                    app.adjacent[(row, col)] = [(row, col + 1), (row-1, col)]
                    app.weight[(row, col)] = [1, 1]
                else:
                    app.adjacent[(row, col)] = [(row, col + 1)]
                    app.weight[(row, col)] = [1]
            elif col == app.cols - 1: # right edge cell
                if ((row - (app.rows - 1)) % 2 == 0):
                    app.adjacent[(row, col)] = [(row, col - 1), (row-1, col)]
                    app.weight[(row, col)] = [1, 1]
                else:
                    app.adjacent[(row, col)] = [(row, col - 1)]
                    app.weight[(row, col)] = [1]
            else: # middle cell
                app.adjacent[(row, col)] = [(row, col + 1), (row, col - 1)]
                app.weight[(row, col)] = [1, 1]
            if row in app.ladders:
                row0, col0, row1, col1 = app.laddersCopy[row]
                if (row, col) == (row0, col0): # cell at bottom of a ladder
                    app.adjacent[(row, col)].append((row1, col1))
                    app.weight[(row, col)].append(1)
            if row in app.snakes:
                row2, col, row3, col3 = app.snakesCopy[row]
                if (row, col) == (row3, col3): # cell at head of a snake
                    app.adjacent[(row, col)].append((row2, col2))
                    app.weight[(row, col)].append(1)
            if (row, col) == (app.winRow, app.winCol):
                if (app.rows % 2 == 0):
                    app.adjacent[(row, col)] = [(row, col + 1)]
                    app.weight[(row, col)] = [1]
                else:
                    app.adjacent[(row, col)] = [(row, col - 1)]
                    app.weight[(row, col)] = [1]

def calculatePath(app, currRow, currCol, targetRow, targetCol):
    initBestPath(app, currRow, currCol)
    graph = {}
    for row in range(app.rows):
        for col in range(app.cols):
            graph[(row, col)] = 999
    graph[(currRow, currCol)] = 0
    path = {}
    unvisited = set([(row, col) for row in range(app.rows) for col in range(app.cols)])
    unvisited.add((currRow, currCol))
    app.startingCell = (currRow, currCol)
    return calculatePathHelper(app, app.startingCell, targetRow, targetCol, graph, path, unvisited)

def calculatePathHelper(app, currCell, targetRow, targetCol, graph, path, unvisited):
    if currCell == (targetRow, targetCol):
        return findBestPath(app, currCell, targetRow, targetCol, path)
    else:
        adjCells = app.adjacent[currCell]
        adjWts = app.weight[currCell]
        for i in range(len(adjCells)):
            adjCell = adjCells[i]
            timeTaken = graph[currCell] + adjWts[i]
            if timeTaken < graph[adjCell]:
                graph[adjCell] = timeTaken
                path[adjCell] = currCell
        unvisited.remove(currCell)
        oldCurrCell = currCell
        # Finding next currCell
        bestHeuristic = 999
        for cell in unvisited:
            row, col = cell
            pythagDist = math.sqrt((col - app.playerCol)**2 + (row - app.playerRow)**2)
            if graph[cell] - pythagDist < bestHeuristic:
                bestHeuristic = graph[cell]
                currCell = cell
        if oldCurrCell == currCell: # cannot find next currCell
            bestPath = []
            return bestPath
        return calculatePathHelper(app, currCell, targetRow, targetCol, graph, path, unvisited)

def findBestPath(app, currCell, targetRow, targetCol, path):
    bestPath = []
    bestPath.append(currCell)
    prevCell = path[currCell]
    bestPath.insert(0, prevCell)
    while prevCell != app.startingCell:
        currCell = prevCell
        prevCell = path[currCell]
        bestPath.insert(0, prevCell)
    return bestPath

#################################################
# Random Generation of Board
#################################################

# inspired from https://www.cs.cmu.edu/~112/notes/notes-recursion-part2.html#nQueens
def generateLadders(app):
    i = random.randint(2, app.cols - 1)
    generateLaddersHelper(app, 1, i)
    solutionIndex = random.randint(0, len(app.allSolutions) - 1)
    app.ladders = app.allSolutions[solutionIndex]

def generateLaddersHelper(app, row0, i):
    # base case
    if row0 >= app.rows: # completed all rows
        return app.allSolutions.append(copy.deepcopy(app.ladders))
    # recursive case
    for col0 in range(i, app.cols):
        for row1 in range(row0 - int(app.rows/3), row0):
            for col1 in range(col0 - int(app.cols/3), col0 + int(app.cols/3)):
                if checkLegal(app, row0, col0, row1, col1):
                    if not checkOverlap(app, row0, col0, row1, col1):
                        app.ladders[row0] = [row0, col0, row1, col1]
                        i = random.randint(0, app.cols - 1)
                        generateLaddersHelper(app, row0 + 2, i)
                        if len(app.allSolutions) >= 1000:
                            return
                        del app.ladders[row0]
    return None

def checkLegal(app, row0, col0, row1, col1):
    if (0 <= row1 < row0 and 0 <= col1 < app.cols and 0 <= col0 < app.cols and
        col0 != col1):
        return True
    return False

def checkOverlap(app, row0, col0, row1, col1):
    grad = (row1 - row0) / (col1 - col0)
    intercept = row0 - grad * col0
    for i in app.ladders:
        row2, col2, row3, col3 = app.ladders[i]
        grad2 = (row3 - row2) / (col3 - col2)
        intercept2 = row2 - grad2 * col2
        if (grad - grad2) != 0: # ladders not parallel
            x = (intercept2 - intercept) / (grad - grad2)
            if (min(col0, col1) < x < max(col0, col1) and
                min(col2, col3) < x < max(col2, col3)):
                 return True
            elif (min(col0, col1) - 1 <= x <= max(col0, col1) + 1 and
                  min(col2, col3) - 1 <= x <= max(col2, col3) + 1 and
                  math.isclose(x, col1) or math.isclose(x, col3)):
                return True
        else: # ladders parallel
            x = intercept2 - intercept
            if math.isclose(x, 0):
                return True
    return False

def generateSnakes(app):
    for i in app.ladders:
        row0, col0, row1, col1 = app.ladders[i]
        newSnakeRow = row0 + (row0 - row1)
        if (newSnakeRow >= app.rows):
            app.snakes[i] = app.rows - 1, col1, row0 - 1, col0
        else:
            if (row0 - 1 == app.winRow and col0 == app.winCol):
                app.snakes[i] = newSnakeRow, col1, row0, col0
            else:
                app.snakes[i] = newSnakeRow, col1, row0 - 1, col0

#################################################
# Gameplay
#################################################

def keyPressed(app, event):
    if app.gameOver == False and app.win == False:
        if (event.key == 'Left'):
            movePlayer(app, -1, 0)
        elif (event.key == 'Right'):
            movePlayer(app, +1, 0)
        elif (event.key == 'Up'):
            if abs(app.playerRow - (app.rows - 1)) % 2 == 0:
                if app.playerCol >= app.cols - 1:
                    movePlayer(app, 0, -1)
            else:
                if app.playerCol <= 0:
                    movePlayer(app, 0, -1)
        elif (event.key == 'p'):
            app.isPaused = not app.isPaused
        elif (event.key == 'Space'):
            app.hasStarted = True
        elif (event.key == 'b'):
            app.buildLadder = True
        elif (event.key == 'g'):
            app.gameOver = True
    else:
        if (event.key == 'r'):
            appStarted(app)

# modifies the position of the player according to user input and
# when the player meets ladder/snake
def movePlayer(app, dcol, drow):
    if (0 <= app.playerCol + dcol < app.cols and
        0 <= app.playerRow + drow < app.rows): # check if within grid
        app.playerCol += dcol
        app.playerRow += drow
        if (app.playerRow, app.playerCol) not in app.visitedCells:
            app.points += 1
            app.visitedCells.add((app.playerRow, app.playerCol))
        for i in range(1, app.rows, 2):
            if (i in app.ladders and
                app.playerRow == app.ladders[i][0] and 
                app.playerCol == app.ladders[i][1]): # meets a ladder
                if (app.playerRow, app.playerCol) not in app.visitedCells:
                    app.points += 1
                if (i == app.lockedLadderIndex): # meets locked ladder
                    if (app.hasKey == True):
                        app.playerRow, app.playerCol = app.ladders[i][2], app.ladders[i][3]
                        app.visitedCells.add((app.ladders[i][2], app.ladders[i][3]))
                else: # meets normal ladder
                    app.playerRow, app.playerCol = app.ladders[i][2], app.ladders[i][3]
                    app.visitedCells.add((app.ladders[i][2], app.ladders[i][3]))
            elif (i in app.snakes and
                  app.playerRow == app.snakes[i][2] and 
                  app.playerCol == app.snakes[i][3]): #meets a snake
                app.playerRow, app.playerCol = app.snakes[i][0], app.snakes[i][1]
                if (app.playerRow, app.playerCol) not in app.visitedCells:
                    app.points += 1
                    app.visitedCells.add((app.snakes[i][2], app.snakes[i][3]))
        # meets a custom ladder
        if (app.madeLadder != [] and 
            (app.playerRow, app.playerCol) == (app.madeLadder[0], app.madeLadder[1])):
            app.playerRow, app.playerCol = app.madeLadder[2], app.madeLadder[3]
            if (app.playerRow, app.playerCol) not in app.visitedCells:
                app.points += 1
                app.visitedCells.add((app.madeLadder[2], app.madeLadder[3]))
            app.madeLadder = []
        if (app.playerRow == app.winRow and app.playerCol == app.winCol): # won game
            app.win = True
        elif app.playerRow <= 2*app.rows/3:
            app.enemyMode = True
            app.enemyStartTime = app.timerCalls
        elif app.playerRow <= 8*app.rows/10:
            app.sabotageMode = True
            app.sabotageStartTime = app.timerCalls
        if (app.playerRow, app.playerCol) == (app.keyRow, app.keyCol):
            app.hasKey = True

def timerFired(app):
    if app.isPaused == False and app.gameOver == False:
        app.timerCalls += 1
        timeGap = 50 * len(app.laddersCopy)
        for i in range(1, app.rows, 2):
            timeGap -= 50
            if timeGap <= app.timerCalls:
                dCalls = app.timerCalls - timeGap
            else:
                dCalls = 0
            if dCalls % 400 == 0:# all disappear
                if i in app.ladders:
                    del app.ladders[i]
                if i in app.snakes:
                    del app.snakes[i]
            elif dCalls % 200 == 0: # snakes appear
                if i in app.ladders:
                    del app.ladders[i]
                if i in app.snakesCopy:
                    app.snakes[i] = app.snakesCopy[i]
            elif dCalls % 100 == 0: # all disappear
                if i in app.ladders:
                    del app.ladders[i]
                if i in app.snakes:
                    del app.snakes[i]
            elif dCalls % 50 == 0: #ladders appear
                if i in app.laddersCopy:
                    app.ladders[i] = app.laddersCopy[i]
                if i in app.snakes:
                    del app.snakes[i]
        # move enemy according to best path calculated earlier
        if (app.enemyMode == True): 
            if (app.playerRow == app.enemyRow and app.playerCol == app.enemyCol): # game over
                app.gameOver = True
            else:
                app.enemyPath = calculatePath(app, app.enemyRow, app.enemyCol, app.playerRow, app.playerCol)
                if app.enemyPath != []:
                    dEnemyCalls = app.timerCalls - app.enemyStartTime
                    if (dEnemyCalls % 5 == 0):
                        app.enemyRow, app.enemyCol = app.enemyPath[1]
                        app.enemyPath.pop(0)
        if app.sabotageMode == True:
            dSabotageCalls = app.timerCalls - app.sabotageStartTime
            if (app.finishSabo == True):
                if (dSabotageCalls % 50 == 0):
                    if app.playerRow - 3 >= 0:
                        app.sabotageRow = random.randint(app.playerRow - 3, app.playerRow)
                        app.finishSabo = False
            else:
                bestRow, bestCol = -2, -2
                if len(app.ladders) != 0:
                    for i in app.ladders: # find nearest ladder
                        ladderRow, ladderCol = app.ladders[i][0], app.ladders[i][1]
                        if ladderRow <= app.sabotageRow:
                            if (abs(app.sabotageRow - ladderRow) <
                                abs(app.sabotageRow - bestRow)):
                                bestRow, bestCol = ladderRow, ladderCol
                if (bestRow, bestCol) != (-2, -2):
                    app.sabotagePath = calculatePath(app, app.sabotageRow,
                                                     app.sabotageCol,
                                                     bestRow, bestCol)
                    if (dSabotageCalls % 5 == 0):
                        app.sabotageRow, app.sabotageCol = app.sabotagePath[1]
                        app.sabotagePath.pop(0)
                        if (app.sabotageRow, app.sabotageCol) == (bestRow, bestCol):
                            del app.ladders[bestRow]
                            del app.laddersCopy[bestRow]
                            app.sabotageRow, app.sabotageCol = -1, -1
                            app.finishSabo = True
        # position of key is any row below locked ladder
        if app.timerCalls % 70 == 0:
            app.keyRow = random.randint(app.lockedLadderIndex, app.rows - 1)
            app.keyCol = random.choice([i for i in range(app.cols) if i != app.lockedLadderIndex])

def mousePressed(app, event):
    if app.hasStarted == False:
        if (app.instrX0 <= event.x <= app.instrX1 and
            app.instrY0 <= event.y <= app.instrY1):
            app.needInstructions = not app.needInstructions
    else:
        if (app.buildLadder == True):
            mouseRow, mouseCol = getCell(app, event.x, event.y)
            pointsReq = abs(mouseRow - app.playerRow) * 5
            if (app.points >= pointsReq and mouseRow != app.playerRow):
                if (0 <= app.playerCol < app.cols - 1):
                    app.madeLadder = [app.playerRow, app.playerCol + 1, mouseRow, mouseCol]
                    if (app.playerRow in app.ladders and
                        app.ladders[app.playerRow][1] == app.playerCol + 1):
                        app.madeLadder = []
                    elif ((app.playerRow + 1) in app.snakes and
                        app.snakes[app.playerRow+1][3] == app.playerCol + 1):
                        app.madeLadder = []
                elif (app.playerCol >= app.cols - 1):
                    app.madeLadder = [app.playerRow, app.playerCol - 1, mouseRow, mouseCol]
                    if (app.playerRow in app.ladders and
                        app.ladders[app.playerRow][1] == app.playerCol - 1):
                        app.madeLadder = []
                    elif ((app.playerRow + 1) in app.snakes and
                        app.snakes[app.playerRow+1][3] == app.playerCol - 1):
                        app.madeLadder = []
                app.buildLadder = False
                app.points -= pointsReq

#################################################
# View
#################################################

# from: https://www.cs.cmu.edu/~112/notes/notes-animations-part1.html#exampleGrids
def getCell(app, x, y):
    row = int((y - app.margin) / app.cellSize)
    col = int((x - app.leftMargin) / app.cellSize)
    return (row, col)

# from: https://www.cs.cmu.edu/~112/notes/notes-animations-part1.html#exampleGrids
def getCellBounds(app, row, col):
    x0 = app.leftMargin + col * app.cellSize
    x1 = app.leftMargin + (col + 1) * app.cellSize
    y0 = app.margin + row * app.cellSize
    y1 = app.margin + (row + 1) * app.cellSize
    return (x0, y0, x1, y1)

# adapted from:
# https://www.cs.cmu.edu/~112/notes/notes-animations-part1.html#exampleGrids
def drawGrid(app, canvas, row, col):
    index = (app.rows * app.cols) + 1
    for row in range(app.rows):
        for col in range(app.cols):
            if row % 2 == 1:
                col = app.cols - 1 - col
            (x0, y0, x1, y1) = getCellBounds(app, row, col)
            index -= 1
            if index % 2 == 1:
                canvas.create_rectangle(x0, y0, x1, y1, fill='#217EA7', width=5)
                if row % 2 == 1:
                    canvas.create_line(x0 + app.cellSize/2, y0 + app.cellSize/4,
                                       x1 - app.cellSize/4, y1 - app.cellSize/2,
                                       width=3, fill='#80C1DE')
                    canvas.create_line(x0 + app.cellSize/2, y1 - app.cellSize/4,
                                       x1 - app.cellSize/4, y1 - app.cellSize/2,
                                       width=3, fill='#80C1DE')
                else:
                    canvas.create_line(x0 + app.cellSize/2, y0 + app.cellSize/2,
                                       x1 - app.cellSize/4, y1 - app.cellSize/4,
                                       width=3, fill='#80C1DE')
                    canvas.create_line(x0 + app.cellSize/2, y0 + app.cellSize/2,
                                       x1 - app.cellSize/4, y0 + app.cellSize/4,
                                       width=3, fill='#80C1DE')
            else:
                canvas.create_rectangle(x0, y0, x1, y1, width=5)
            # draw index
            fontSize = int(app.cellSize/4)
            canvas.create_text(x0 + app.cellSize/3, y0 + app.cellSize/3,
                               text=str(index), font=f'Lucida {fontSize}')
    # draw starting cell
    x0, y0, x1, y1 = getCellBounds(app, app.rows - 1, -1)
    canvas.create_rectangle(x0, y0, x1, y1, width=5)

def drawPlayer(app, canvas):
    row, col = app.playerRow, app.playerCol
    x0, y0, x1, y1 = getCellBounds(app, row, col)
    Cx, Cy = (x0+x1)/2, (y0+y1)/2
    smallR = app.cellSize/3
    bigR = 2*app.cellSize/5
    canvas.create_oval(Cx-bigR, Cy-smallR, Cx+bigR, Cy+smallR, fill='pink', outline='')
    canvas.create_text(Cx, Cy, text='U W U', font=f'Arial {int(app.cellSize/5)}')

def drawEnemy(app, canvas):
    row, col = app.enemyRow, app.enemyCol
    x0, y0, x1, y1 = getCellBounds(app, row, col)
    Cx, Cy = (x0+x1)/2, (y0+y1)/2
    smallR = app.cellSize/3
    bigR = 2*app.cellSize/5
    canvas.create_oval(Cx-bigR, Cy-smallR, Cx+bigR, Cy+smallR, fill='purple', outline='')
    leftX, rightX = Cx-bigR/3, Cx+bigR/3
    # left tooth
    canvas.create_polygon(leftX, Cy, Cx, Cy, (leftX+Cx)/2, Cy+smallR/2, fill='white')
    # right tooth
    canvas.create_polygon(Cx, Cy, rightX, Cy, (Cx+rightX)/2, Cy+smallR/2, fill='white')
    # eyes
    eyeR = app.cellSize/16
    leftEyeX, leftEyeY = leftX, Cy-smallR/3
    rightEyeX, rightEyeY = rightX, leftEyeY
    canvas.create_oval(leftEyeX-eyeR, leftEyeY-eyeR, leftEyeX+eyeR, leftEyeY+eyeR,
                        fill='red', outline='')
    canvas.create_oval(rightEyeX-eyeR, rightEyeY-eyeR, rightEyeX+eyeR, rightEyeY+eyeR,
                        fill='red', outline='')
    
def drawSabotage(app, canvas):
    if 0 <= app.sabotageRow < app.rows and 0 <= app.sabotageCol < app.cols:
        row, col = app.sabotageRow, app.sabotageCol
        x0, y0, x1, y1 = getCellBounds(app, row, col)
        Cx, Cy = (x0+x1)/2, (y0+y1)/2
        smallR = app.cellSize/3
        bigR = 2*app.cellSize/5
        canvas.create_oval(Cx-bigR, Cy-smallR, Cx+bigR, Cy+smallR, fill='yellow', outline='')
        leftX, rightX = Cx-bigR/3, Cx+bigR/3
        canvas.create_line(leftX, Cy, rightX, Cy, fill='black')
        arcR = abs(Cx-rightX)/2
        canvas.create_arc(Cx, Cy-arcR, rightX, Cy+arcR, start=180, extent=180, fill='pink')
        # eyes
        eyeR = app.cellSize/16
        leftEyeX, leftEyeY = leftX, Cy-smallR/3
        rightEyeX, rightEyeY = rightX, leftEyeY
        canvas.create_oval(leftEyeX-eyeR, leftEyeY-eyeR, leftEyeX+eyeR, leftEyeY+eyeR,
                            fill='black', outline='')
        canvas.create_oval(rightEyeX-eyeR, rightEyeY-eyeR, rightEyeX+eyeR, rightEyeY+eyeR,
                            fill='black', outline='')

def drawLadder(app, canvas):
    lineWidth = int(app.cellSize/10)
    ladMargX = app.cellSize / 4
    ladMargY = 3 * app.cellSize / 5
    for i in app.ladders:
        row0, col0, row1, col1 = app.ladders[i]
        x0, y0, x1, y1 = getCellBounds(app, row0, col0)
        x2, y2, x3, y3 = getCellBounds(app, row1, col1)
        if (i == app.lockedLadderIndex):
            ladderColor = 'brown'
        else:
            ladderColor = '#EEA60B'
        canvas.create_line(x0+ladMargX, y0+ladMargY, x2+ladMargX, y3-ladMargY,
                        fill=ladderColor, width=lineWidth)
        canvas.create_line(x1-ladMargX, y0+ladMargY, x3-ladMargX, y3-ladMargY,
                        fill=ladderColor, width=lineWidth)
    if app.madeLadder != []:
        row0, col0, row1, col1 = app.madeLadder
        x0, y0, x1, y1 = getCellBounds(app, row0, col0)
        x2, y2, x3, y3 = getCellBounds(app, row1, col1)
        canvas.create_line(x0+ladMargX, y0+ladMargY, x2+ladMargX, y3-ladMargY,
                            fill='brown', width=lineWidth)
        canvas.create_line(x1-ladMargX, y0+ladMargY, x3-ladMargX, y3-ladMargY,
                            fill='brown', width=lineWidth)

def drawKey(app, canvas):
    if (app.hasKey == False):
        row, col = app.keyRow, app.keyCol
        x0, y0, x1, y1 = getCellBounds(app, row, col)
        keyR = app.cellSize / 8
        margin = app.cellSize/9
        keyCx, keyCy = x0 + app.cellSize/2, y1 - (keyR + margin)
        canvas.create_oval(keyCx-keyR, keyCy-keyR, keyCx+keyR, keyCy+keyR,
                           fill='', outline='brown', width=int(margin))
        bladeWidth = 2*keyR/3
        bladeLength = (keyCy-keyR)-(y0+margin)
        canvas.create_rectangle(keyCx-bladeWidth/2, y0+margin,
                                keyCx+bladeWidth/2, keyCy-keyR,
                                fill='brown', outline='')
        notchWidth = bladeWidth*2
        notchHeight = bladeLength/8
        canvas.create_rectangle(keyCx+bladeWidth/2, y0+margin+bladeLength/8,
                                keyCx+bladeWidth/2+notchWidth, y0+margin+bladeLength/8+notchHeight,
                                fill='brown', outline='')
        canvas.create_rectangle(keyCx+bladeWidth/2, y0+margin+3*bladeLength/8,
                                keyCx+bladeWidth/2+notchWidth, y0+margin+3*bladeLength/8+notchHeight,
                                fill='brown', outline='')
def drawSnake(app, canvas):
    for i in app.snakes:
        row0, col0, row1, col1 = app.snakes[i]
        x0, y0, x1, y1 = getCellBounds(app, row0, col0) #tail bounds
        x2, y2, x3, y3 = getCellBounds(app, row1, col1) #headbounds
        tailX, tailY = x0 + app.cellSize/2, y0 + app.cellSize/2
        headX, headY = x2 + app.cellSize/2, y2 + 3*app.cellSize/4
        drawSnakeHelper(app, canvas, tailX, tailY, headX, headY)

def drawSplashScreen(app, canvas):
    canvas.create_rectangle(0, 0, app.width, app.height, fill='light blue')
    canvas.create_text(app.width/2, 2*app.height/5,
                       text='Snakes and Ladders', font='Lucida 28 bold')
    canvas.create_text(app.width/2, app.height/2,
                       text='Reinvented', font='Lucida 28 bold')
    canvas.create_text(app.width/2, 3*app.height/5,
                       text='Press Space to Start', font='Lucida 18 italic')
    # draw design
    # draw ladder
    newMargin = 10*app.margin
    x0, y0 = 2*app.margin, app.height - newMargin
    x1, y1 = x0, y0 - app.height/4
    x2, y2 = 2*app.margin + app.width/10, app.height - newMargin
    x3, y3 = 2*app.margin + app.width/10, app.height - newMargin - app.height/4  
    drawVertLadder(app, canvas, newMargin, x0, y0, x1, y1, x2, y2, x3, y3)
    a0, b0 = app.width - 2*app.margin - app.width/10, app.height - newMargin
    a1, b1 = app.width - 2*app.margin - app.width/10, app.height - newMargin - app.height/4
    a2, b2 = app.width - 2*app.margin, app.height - newMargin
    a3, b3 = app.width - 2*app.margin, app.height - newMargin - app.height/4
    drawVertLadder(app, canvas, newMargin, a0, b0, a1, b1, a2, b2, a3, b3)
    # draw snake
    tailX, tailY = app.margin, app.height - 10*app.margin
    headX, headY = app.margin + app.width/5, app.height - 10*app.margin - app.height/5
    drawSnakeHelper(app, canvas, tailX, tailY, headX, headY)
    tail2X, tail2Y = app.width - app.margin, app.height - 10*app.margin
    head2X, head2Y = app.width - app.margin - app.width/5, app.height - 10*app.margin - app.height/5
    drawSnakeHelper(app, canvas, tail2X, tail2Y, head2X, head2Y)
    # instructions button
    canvas.create_rectangle(app.instrX0, app.instrY0, app.instrX1, app.instrY1, fill='navy')
    canvas.create_text((app.instrX0+app.instrX1)/2, (app.instrY0+app.instrY1)/2, text='?',
                        font=f'Lucida {int(2*app.instrWidth/3)} bold', fill='light blue')
    drawInstructions(app, canvas)

def drawVertLadder(app, canvas, newMargin, x0, y0, x1, y1, x2, y2, x3, y3):
    canvas.create_line(x0, y0, x1, y1, fill='brown', width=5)
    canvas.create_line(x2, y2, x3, y3, fill='brown', width=5)
    spacing = (app.height/4)/5
    numLadders = int((app.height/4)/spacing)
    for i in range(numLadders - 1):
        canvas.create_line(x0, y0 - (i+1)*spacing, x2, y2 - (i+1)*spacing, fill='brown', width=5)

def drawSnakeHelper(app, canvas, tailX, tailY, headX, headY):
    # intermediate points
    Ax, Ay = min(headX, tailX) + 3*abs(headX-tailX)/8, headY + (tailY-headY)/8
    Bx, By = min(headX, tailX) + 5*abs(headX-tailX)/8, headY + 7*(tailY-headY)/8
    canvas.create_line(headX, headY, Ax, Ay, Bx, By, tailX, tailY,
                        smooth='true', fill='#51B40B', width=int(app.cellSize/10))
    # draw head
    headR = app.cellSize/7
    canvas.create_oval(headX-headR, headY-headR, headX+headR, headY+headR,
                        fill='#51B40B', outline='')
    eyeR = headR/5
    canvas.create_oval(headX-eyeR, headY-eyeR, headX+eyeR, headY+eyeR,
                        fill='black', outline='')
    # draw tongue
    if headX > tailX:
        leftTongX, leftTongY = headX + headR, headY
        canvas.create_line(leftTongX, leftTongY, leftTongX+headR, leftTongY, fill='red')
        topForkX, topForkY = leftTongX + 3*headR/2, headY + headR/2
        btmForkX, btmForkY = topForkX, headY - headR/2
        canvas.create_line(leftTongX+headR, leftTongY, topForkX, topForkY, fill='red')
        canvas.create_line(leftTongX+headR, leftTongY, btmForkX, btmForkY, fill='red')
    else:
        leftTongX, leftTongY = headX - headR, headY
        canvas.create_line(leftTongX, leftTongY, leftTongX-headR, leftTongY, fill='red')
        topForkX, topForkY = leftTongX - 3*headR/2, headY + headR/2
        btmForkX, btmForkY = topForkX, headY - headR/2
        canvas.create_line(leftTongX-headR, leftTongY, topForkX, topForkY, fill='red')
        canvas.create_line(leftTongX-headR, leftTongY, btmForkX, btmForkY, fill='red')

def drawInstructions(app, canvas):
    if app.needInstructions == True:
        canvas.create_rectangle(app.margin*2, app.margin*2,
                                app.width-app.margin*2, app.height-app.margin*2,
                                fill='light blue')
        fontSize = int(app.cellSize/2)
        canvas.create_text(app.width/2, app.margin*2+fontSize, text='Instructions',
                            font=f'Lucida {fontSize} bold underline')
        fontSize2 = int(app.cellSize/4)
        canvas.create_text(app.margin*3, app.margin*2+fontSize*2,
                           text='Gameplay:',
                           font=f'Lucida {fontSize2} bold', anchor='w')
        gameplay = '''
Use left, right and up arrow keys to move avatar
Press ‘p’ to pause the game
Do not get caught by the evil purple enemy!
Use ladders before the yellow enemy removes them!
One special locked ladder can only be used if you have the key.
'''
        canvas.create_text(app.margin*3, app.margin*2+fontSize*4,
                           text=gameplay,
                           font=f'Lucida {fontSize2}', anchor='w')
        canvas.create_text(app.margin*3, app.margin*2+fontSize*6.5,
                           text='Earning points:',
                           font=f'Lucida {fontSize2} bold', anchor='w')
        pointsInstr = '''
Visiting a cell gives you 1 point.
Revisiting the cell does not give additional points.
You may earn a maximum of 100 points.
'''
        canvas.create_text(app.margin*3, app.margin*2+fontSize*8,
                           text=pointsInstr,
                           font=f'Lucida {fontSize2}', anchor='w')
        canvas.create_text(app.margin*3, app.margin*2+fontSize*10,
                           text='Building ladders:',
                           font=f'Lucida {fontSize2} bold', anchor='w')
        buildInstr = '''
Press ‘b’ and click on desired cell you want the ladder to extend to.
Ladder building cost points!
Points are computed by (no. of rows traversed)*5
'''
        canvas.create_text(app.margin*3, app.margin*2+fontSize*11.5,
                           text=buildInstr,
                           font=f'Lucida {fontSize2}', anchor='w')
        canvas.create_text(app.margin*3, app.margin*2+fontSize*13,
                           text='Have fun!',
                           font=f'Lucida {fontSize2}', anchor='w')

def redrawAll(app, canvas):
    if app.hasStarted:
        drawGrid(app, canvas, app.rows, app.cols)
        if app.win:
            canvas.create_rectangle(app.width/4, 2*app.height/5,
                                    3*app.width/4, 3*app.height/5, fill='light blue')
            canvas.create_text(app.width/2, app.height/2 - 10, text='You Win!',
                                font='Lucida 30 bold')
            canvas.create_text(app.width/2, app.height/2 + 20, text='Press r to play again',
                                font='Lucida 20 italic')
        elif app.gameOver:
            canvas.create_rectangle(app.width/4, 2*app.height/5,
                                    3*app.width/4, 3*app.height/5, fill='light blue')
            canvas.create_text(app.width/2, app.height/2 - 10, text='Game Over!',
                                font='Lucida 30 bold')
            canvas.create_text(app.width/2, app.height/2 + 20, text='Press r to restart',
                                font='Lucida 20 italic')
        else:
            drawLadder(app, canvas)
            drawSnake(app, canvas)
            drawKey(app, canvas)
            drawPlayer(app, canvas)
            if app.enemyMode:
                drawEnemy(app, canvas)
            if app.sabotageMode:
                drawSabotage(app, canvas)
            # draw score
            canvas.create_text(app.width - app.margin, app.margin/2, text=f'Score:{app.points}', anchor='e')
    else:
        drawSplashScreen(app, canvas)

playSnL()