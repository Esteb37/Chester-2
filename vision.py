#Vision Library for Chester Adaptive Robotic Chess Player
#Author: Esteban Padilla Cerdio
#Version: 1.5

#------------------------Libraries--------------------------
import numpy as np
from skimage.measure import compare_ssim
import cv2
import msvcrt
from chess import square
from time import sleep

#---------------------Setup vision---------------------------

def start():
    global cap, ret, img, rows, cols, depth, center_squares, empty_squares,ranges,columns, recal
    global row_num = 8 #Number of rows in a chessboard
    cap = cv2.VideoCapture(1) #Webcams tend to occupy port 1
    ret, img= cap.read()
    rows, cols, depth= img.shape
    center_squares = [[x*46+21 for x in range(0,row_num)],[y*46+41 for y in range(0,row_num)]]
    empty_squares = {}
    ranges=[range(14,48),range(60,94),range(106,140),range(152,186),range(198,232),range(244,278),range(290,324),range(336,370)]
    columns = "HGFEDCBA"
    global board_grid
    board_grid = np.zeros((img.shape), np.uint8)
    board_grid = create_board(board_grid)
    recal = input("Would you like to re-calibrate? (y/n):\n")
    global M
    if recal in "yY":
        recalibrated = True
        M = calibrate_cam()
    elif recal in "nN":
        recalibrated = False
        M =  np.load("calibrate.npy")
        global board_image
        board_image = np.load("board.npy")
    global before_image
    ret, before_image = cap.read()
    before_image = cv2.warpPerspective(before_image,M,(cols,rows))
    before_image = before_image[0:384,0:384]
    return recalibrated

#--------------Digital display functions---------------------

#Display chessboard
def display_board(board,moving):
    global l_img,b_rows,brd,selected
    brd = board
    selected = ""
    cv2.namedWindow("Board",cv2.WINDOW_AUTOSIZE)
    b_rows = str(board.epd).split("'")[1].split(" ")[0].split("/")
    l_img = cv2.imread("GUI\\board.png")

    for y in range(8):
        x = 0

        for ch in b_rows[y]:
            try:
                x+=int(ch)
            except:
                if ch in "prkqbn":
                    color = "b"
                else:
                    color = "w"
                path = "GUI\\"+ch+color+".png"
                s_img = cv2.imread(path, -1)
                x_offset = x*70+30
                y_offset = y*70
                y1, y2 = y_offset, y_offset + s_img.shape[0]
                x1, x2 = x_offset, x_offset + s_img.shape[1]

                alpha_s = s_img[:, :, 3] / 255.0
                alpha_l = 1.0 - alpha_s

                for c in range(0, 3):
                    l_img[y1:y2, x1:x2, c] = (alpha_s * s_img[:, :, c] +alpha_l * l_img[y1:y2, x1:x2, c])
                x+=1
    if moving:
        cv2.setMouseCallback('Board',select_piece)
        while(True):
            cv2.imshow('Board',l_img)
            k = cv2.waitKey(20) & 0xFF
            if k == ord(' ') or len(selected)>=4:
                return selected
            if k == 26:
                return 26
    else:
        show_image("Board",l_img)
#Detect mouse click on piece
def select_piece(event,x,y,flags,param):
    global l_img,b_rows,brd,selected
    if event == cv2.EVENT_LBUTTONDBLCLK:
        x = ((x-30)//70)
        y = (9-(y+70)//70)
        if str(brd.piece_at(square(x,y-1))) in "QNRKPB" or len(selected)!=0:
            selected+= "abcdefgh"[x]+str(y)
            x = x*70+65
            y = (8-y)*70+35
            l_img = cv2.rectangle(l_img,(x-35,y-35),(x+35,y+35),(0,255,0),3)
#Display messages such as "illegal move"
def message(msg):
    font = cv2.FONT_HERSHEY_SIMPLEX
    ill = cv2.putText(l_img,msg,(100,300), font, 2,(0,0,255),10,cv2.LINE_AA)
    show_image("Board",ill)
    sleep(0.3)
#Display an image
def show_image(name, img):
    while True:
        try:
            cv2.imshow(name,img)
            if cv2.waitKey(1) & 0xFF == ord('y'):
                cv2.imwrite('images/c1.png',frame)
                cv2.destroyAllWindows()
            break
        except NameError:
            continue

#------------Camera calibration functions-------------------

#Smooth out picture
def erase_shadows(img):
    rgb_planes = cv2.split(img)
    result_planes = []
    for plane in rgb_planes:
        dilated_img = cv2.dilate(plane, np.ones((7,7), np.uint8))
        bg_img = cv2.medianBlur(dilated_img, 21)
        diff_img = 255 - cv2.absdiff(plane, bg_img)
        result_planes.append(diff_img)
    result = cv2.merge(result_planes)
    return result
#Calculate cosine
def angle_cos(p0, p1, p2):
    d1, d2 = (p0-p1).astype('float'), (p2-p1).astype('float')
    return abs( np.dot(d1, d2) / np.sqrt( np.dot(d1, d1)*np.dot(d2, d2) ) )
#Find all the squares in the picture
def find_squares(img):
    img = cv2.GaussianBlur(img, (5, 5), 0)
    squares = []
    for gray in cv2.split(img):
        for thrs in range(0, 255, 26):
            if thrs == 0:
                bin = cv2.Canny(gray, 0, 50, apertureSize=5)
                bin = cv2.dilate(bin, None)
            else:
                _retval, bin = cv2.threshold(gray, thrs, 255, cv2.THRESH_BINARY)
            bin, contours, _hierarchy = cv2.findContours(bin, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                cnt_len = cv2.arcLength(cnt, True)
                cnt = cv2.approxPolyDP(cnt, 0.02*cnt_len, True)
                if len(cnt) == 4 and cv2.contourArea(cnt) > 1000 and cv2.isContourConvex(cnt):
                    cnt = cnt.reshape(-1, 2)
                    max_cos = np.max([angle_cos( cnt[i], cnt[(i+1) % 4], cnt[(i+2) % 4] ) for i in range(4)])
                    if max_cos < 0.1:
                        squares.append(cnt)
    return squares
#Automatically detect board and find rate of transformation
def find_M(img,board_grid):
    squares = find_squares(img)
    largest = []
    for x in squares:
        area = ((x[0][0]*x[1][1])-(x[0][1]*x[1][0])+(x[1][0]*x[2][1])-(x[1][1]*x[2][0])+(x[2][0]*x[3][1])-(x[2][1]*x[3][0])+(x[3][0]*x[0][1])-(x[3][1]*x[0][0]))/2
        area = abs(area)
        if area>img.size/64:
            midpoint = ((x[0][0]+x[2][0])/2,(x[0][1]+x[2][1])/2)
            largest.append([x,midpoint])

    possibles = []
    for x in largest:
        originalBlank = board_grid.copy()
        originalImg = img.copy()
        corners =  np.float32([[0,0],[384,0],[0,384],[384,384]])
        boardCorners = [[x[0][0][0],x[0][0][1]],[x[0][1][0],x[0][1][1]],[x[0][2][0],x[0][2][1]],[x[0][3][0],x[0][3][1]]]
        boardCorners = sorted(boardCorners, key=lambda x: x[0])
        boardCorners = sorted([boardCorners[0],boardCorners[1]], key=lambda x: x[1])+sorted([boardCorners[2],boardCorners[3]], key=lambda x: x[1])
        boardCorners=  np.float32([boardCorners[0],boardCorners[2],boardCorners[1],boardCorners[3]])
        M = cv2.getPerspectiveTransform(corners,boardCorners)
        board_grid = cv2.warpPerspective(board_grid,M,(cols,rows))
        combined = cv2.addWeighted(board_grid, 0.5, img, 0.5, 0, img)
        show_image("Calculating", combined)
        M = cv2.getPerspectiveTransform(boardCorners,corners)
        img = cv2.warpPerspective(img,M,(cols,rows))
        squares = find_squares(img)
        midpoints= []
        for x in squares:
            midpoint = ((x[0][0]+x[2][0])/2,(x[0][1]+x[2][1])/2)
            midpoints.append(midpoint)
        score = 0
        for x in boardMidpoints:
            if x in midpoints:
                score+=1
        possibles.append([img,score,M])
        board_grid = originalBlank
        img = originalImg
    possibles = sorted(possibles, key=lambda x: x[1])
    cv2.destroyAllWindows()
    return possibles[len(possibles)-1][2]
#Create grid to display over transformed board
def create_board(board_grid):
    for y in range(8):
        for x in range(8):
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(board_grid,columns[x]+str(y+1),(x*46+36,y*46+33), font, 0.5,(255,255,255),1,cv2.LINE_AA)
    global boardMidpoints
    boardMidpoints = []
    for x in range(8):
        for y in range(8):
            mids = [((x*46+30),(y*46+30)),((x*46+31),(y*46+30)),((x*46+32),(y*46+30)),((x*46+30),(y*46+31)),((x*46+31),(y*46+31)),((x*46+32),(y*46+31)),((x*46+30),(y*46+32)),((x*46+31),(y*46+32)),((x*46+32),(y*46+32))]
            for midpoint in mids:
                boardMidpoints.append(midpoint)
                board_grid = cv2.line(board_grid, midpoint,midpoint, (0,255,0), 3)
    board_grid2 = board_grid[0:384, 0:384]
    return board_grid
#Draw a circle where mouse clicks
def draw_circle(event,x,y,flags,param):
    global mouseX,mouseY
    if event == cv2.EVENT_LBUTTONDBLCLK:
        cv2.circle(drawable,(x,y),3,(0,255,0),-1)
        boardCorners.append([x,y])
#Select corners of board to find rate of transformation
def draw_M(img):
    global drawable
    drawable = img
    global boardCorners
    boardCorners = []
    show_image("Draw",drawable)
    cv2.setMouseCallback('Draw',draw_circle)
    corners =  np.float32([[0,0],[384,0],[0,384],[384,384]])
    while(True):
        cv2.imshow('Draw',drawable)
        k = cv2.waitKey(20) & 0xFF
        if k == 27 or len(boardCorners)==4:
            break
    boardCorners = sorted(boardCorners, key=lambda x: x[0])
    boardCorners = sorted([boardCorners[0],boardCorners[1]], key=lambda x: x[1])+sorted([boardCorners[2],boardCorners[3]], key=lambda x: x[1])
    boardCorners=  np.float32([boardCorners[0],boardCorners[2],boardCorners[1],boardCorners[3]])
    M = cv2.getPerspectiveTransform(boardCorners,corners)
    cv2.destroyAllWindows()
    return M
#Transform camera image to fit board in grid
def calibrate_cam():
    while True:
        ret, vid = cap.read()
        imgray = cv2.cvtColor(vid,cv2.COLOR_BGR2GRAY)
        ret,thresh = cv2.threshold(imgray,127,255,0)
        im2, contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(vid, contours, -1, (0,255,0), 3)
        if msvcrt.kbhit() and msvcrt.getwch() == "\r":
            cv2.destroyAllWindows()
            ret, img = cap.read()
            break
        else:
            pass
        show_image("Fit board", vid)
    mode = input("Manual or automatic? (m/a)")
    if mode in "aA":
        M = find_M(img,board_grid)
    else:
        M = draw_M(img)
    global board_image
    ret, board_image = cap.read()
    for leter in columns.lower():
        for number in range(1,9):
            empty_squares[leter+str(number)] = True
    np.save("board.npy",board_image)
    np.save("calibrate.npy",M)
    while True:
        ret, vid = cap.read()
        vid = cv2.warpPerspective(vid,M,(384,384))
        grid = board_grid
        grid = grid[0:384,0:384]
        vid = cv2.addWeighted(grid, 0.5, vid, 0.5, 0, vid)
        if msvcrt.kbhit() and msvcrt.getwch() == "\r":
            cv2.destroyAllWindows()
            break
        else:
            pass
        show_image("Place pieces",vid)
    return M

#--------------Movement detection functions-----------------
#Detect changes between images
def compare(img1,img2):
    imageA = erase_shadows(img1.copy())
    imageB = erase_shadows(img2.copy())
    grayA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
    grayB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
    (score, diff) = compare_ssim(grayA, grayB, full=True)
    diff = (diff * 255).astype("uint8")
    thresh = cv2.threshold(diff, 0, 255,cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    thresh, contours, hierarchy= cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    show_image("Thresh",thresh)
    return  thresh
#Return possible movements
def get_move():
    ret, after = cap.read()
    after = cv2.warpPerspective(after,M,(cols,rows))
    after = after[0:384,0:384]
    squares = []
    possibles = []
    global before_image
    before = before_image
    difference = compare(before,after)

    grid = board_grid
    grid=grid[0:384,0:384]
    for x in range(8):
        for y in range(8):
            square = difference[center_squares[0][x]:center_squares[1][x],center_squares[0][y]:center_squares[1][y]]
            if np.average(square)>100:
                squares.append(columns[y].lower()+str(x+1))
    for fro in squares:
        for to in squares:
            if fro!=to:
                possibles.append(fro+to)
    before_image = after
    return possibles
#Detect change in empty squares in case of error
def run_backup():
    board = board_image.copy()
    board = cv2.warpPerspective(board,M,(cols,rows))
    board = board[0:384,0:384]
    ret, bin = cap.read()
    after = bin.copy()
    after = cv2.warpPerspective(after,M,(cols,rows))
    after = after[0:384,0:384]
    difference = compare(board,after)
    new_empty = empty_squares.copy()
    for x in range(8):
        for y in range(8):
            square = difference[center_squares[0][x]:center_squares[1][x],center_squares[0][y]:center_squares[1][y]]
            if np.average(square)>100:
                new_empty[columns[y].lower()+str(x+1)]=False
            else:
                new_empty[columns[y].lower()+str(x+1)]=True
    return new_empty

#------------------------Deprecated--------------------------
#Highlight movements on grid
"""def draw_image(userMove):
    ret, after = cap.read()
    after = cv2.warpPerspective(after,M,(cols,rows))
    after = after[0:384,0:384]
    squares = []
    possibles = []
    grid = board_grid
    grid=grid[0:384,0:384]
    combined = cv2.addWeighted(grid, 0.5, after, 0.5, 0, after)
    board_grid = cv2.line(board_grid, midpoint,midpoint, (0,255,0), 3)
    combined = cv2.rectangle(combined,((8-((ord(userMove[0]))- 96))*46+8,(int(userMove[1])-1)*46+8),((8-((ord(userMove[0]))- 96))*46+54,(int(userMove[1])-1)*46+54),(0,255,0),3)
    combined = cv2.rectangle(combined,((8-((ord(userMove[2]))- 96))*46+8,(int(userMove[3])-1)*46+8),((8-((ord(userMove[2]))- 96))*46+54,(int(userMove[3])-1)*46+54),(0,0,255),3)
    show_image("Combined",combined)"""
