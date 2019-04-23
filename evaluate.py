#Board evaluation Library for Chester Adaptive Robotic Chess Player
#Author: Esteban Padilla Cerdio
#Currently unused
#Version: 1.0

#------------------Board evaluation functuions------------------

#Calculate score of the board in terms of positive white and negative black
def boardValue():
    doubledBlack =0
    doubledWhite =0
    isolatedBlack =8
    isolatedWhite = 8
    blockedBlack = 0
    blockedWhite = 0
    score = 0
    for x in range(8):
        for y in range(8):
            piece= board.piece_at(chess.square(y,x))
            if piece!=None:
                if piece.symbol() in "pnbrqk":
                    if piece.symbol() =="p":
                        if  board.piece_at(chess.square(y,x-1))!=None and board.piece_at(chess.square(y,x-1)).symbol() =="p":
                            doubledBlack +=1
                        if x!=0 and board.piece_at(chess.square(y,x-1))!=None:
                            blockedBlack+=1
                    score-= pstB[piece.symbol()][chess.square(y,x)]
                if piece.symbol() in "PNBRQK":
                    if piece.symbol() =="P":
                        if  board.piece_at(chess.square(y,x+1))!=None and board.piece_at(chess.square(y,x+1)).symbol() =="P":
                            doubledWhite +=1
                        if x!=7 and board.piece_at(chess.square(y,x+1))!=None:
                            blockedWhite+=1
                    score+= pstW[piece.symbol()][chess.square(y,x)]
    score+=32767*(len(board.pieces(6,True))-len(board.pieces(6,False)))
    score+=975*(len(board.pieces(5,True))-len(board.pieces(5,False)))
    score+=500*(len(board.pieces(4,True))-len(board.pieces(4,False)))
    score+=325*(len(board.pieces(3,True))-len(board.pieces(3,False)))
    score+=320*(len(board.pieces(2,True))-len(board.pieces(2,False)))
    score+=100*(len(board.pieces(1,True))-len(board.pieces(1,False)))
    score-=25 *(doubledWhite-doubledBlack+blockedWhite-blockedWhite)
    return score
#Find best possible move based on boardValue
def findBest(isBlack):
    if isBlack:
        score=100000
    else:
        score=-100000
    fen = board.fen()
    for move in board.legal_moves:
        board.push(move)
        if isBlack and boardValue()<score:
            bestMove = move
            score = boardValue()
        elif not isBlack and boardValue()>score:
            bestMove = move
            score = boardValue()
        board.set_fen(fen)
    return bestMove
#Find the best possible move beyond next
def futureBest(isBlack):
    if isBlack:
        score = 10000
    else:
        score =-10000
    fen = board.fen()
    for move in board.legal_moves:
        board.push(move)
        board.push(findBest(isBlack))
        fen2 = board.fen()
        for move2 in board.legal_moves:
            board.push(move2)
            if isBlack and boardValue()<score:
                score = boardValue()
                bestMove = move
            elif not isBlack and boardValue()>score:
                score = boardValue()
                bestMove = move
            board.set_fen(fen2)
        board.set_fen(fen)
    return bestMove
#Create computer move
def generateMove(isBlack):
    fen = board.fen()
    if isBlack:
        score = 100000
    else:
        score =-100000
    for move in board.legal_moves:
        board.push(move)
        board.push(futureBest(not isBlack))
        fen2 = board.fen()
        for move2 in board.legal_moves:
            board.push(move2)
            if isBlack and boardValue()<score:
                bestMove = move
                score = boardValue()
            elif not isBlack and boardValue()>score:
                bestMove = move
                score = boardValue()
            board.set_fen(fen2)
        board.set_fen(fen)
    return bestMove


#------------------------Points by piece----------------------
pstB = {
    'p': [    0,  0,  0,  0,  0,  0,  0,  0,
            50, 50, 50, 50, 50, 50, 50, 50,
            10, 10, 20, 30, 30, 20, 10, 10,
             5,  5, 10, 27, 27, 10,  5,  5,
             0,  0,  0, 25, 25,  0,  0,  0,
             5, -5,-10,  0,  0,-10, -5,  5,
             5, 10, 10,-25,-25, 10, 10,  5,
             0,  0,  0,  0,  0,  0,  0,  0],
    'n': [ -50,-40,-30,-30,-30,-30,-40,-50,
            -40,-20,  0,  0,  0,  0,-20,-40,
            -30,  0, 10, 15, 15, 10,  0,-30,
            -30,  5, 15, 20, 20, 15,  5,-30,
            -30,  0, 15, 20, 20, 15,  0,-30,
            -30,  5, 10, 15, 15, 10,  5,-30,
            -40,-20,  0,  5,  5,  0,-20,-40,
            -50,-40,-20,-30,-30,-20,-40,-50],
    'b': [-20,-10,-10,-10,-10,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0,  5, 10, 10,  5,  0,-10,
            -10,  5,  5, 10, 10,  5,  5,-10,
            -10,  0, 10, 10, 10, 10,  0,-10,
            -10, 10, 10, 10, 10, 10, 10,-10,
            -10,  5,  0,  0,  0,  0,  5,-10,
            -20,-10,-40,-10,-10,-40,-10,-20],
    'r': [  35,  29,  33,   4,  37,  33,  56,  50,
            55,  29,  56,  67,  55,  62,  34,  60,
            19,  35,  28,  33,  45,  27,  25,  15,
             0,   5,  16,  13,  18,  -4,  -9,  -6,
           -28, -35, -16, -21, -13, -29, -46, -30,
           -42, -28, -42, -25, -25, -35, -26, -46,
           -53, -38, -31, -26, -29, -43, -44, -53,
           -30, -24, -18,   5,  -2, -18, -31, -32],
    'q': [   6,   1,  -8,-104,  69,  24,  88,  26,
            14,  32,  60, -10,  20,  76,  57,  24,
            -2,  43,  32,  60,  72,  63,  43,   2,
             1, -16,  22,  17,  25,  20, -13,  -6,
           -14, -15,  -2,  -5,  -1, -10, -20, -22,
           -30,  -6, -13, -11, -16, -11, -16, -27,
           -36, -18,   0, -19, -15, -15, -21, -38,
           -39, -30, -31, -13, -31, -36, -34, -42],
    'k': [   4,  54,  47, -99, -99,  60,  83, -62,
           -32,  10,  55,  56,  56,  55,  10,   3,
           -62,  12, -57,  44, -67,  28,  37, -31,
           -55,  50,  11,  -4, -19,  13,   0, -49,
           -55, -43, -52, -28, -51, -47,  -8, -50,
           -47, -42, -43, -79, -64, -32, -29, -32,
            -4,   3, -14, -50, -57, -18,  13,   4,
            17,  30,  -3, -14,   6,  -1,  40,  18],
            }
def invert(piece):
    square = []
    for x in range(8):
        row=[]
        for y in range(8):
            row.append(pstB[piece][x*8+y])
        square.insert(0,row)
    for x in square:
        for y in range(len(x)):
            pstW[piece.upper()].append(x[y])
for x in pstB.keys():
    invert(x)
pstW={"P":[],"N":[],"B":[],"R":[],"Q":[],"K":[]}
