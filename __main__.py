from chester import Chester
from engine import StockfishPlayer
from chess import Move
from vision import message,get_move,run_backup
#import app


def main():
    while True:
        chester.display(False) #Display position of pieces, False means user is not moving
        #Digital mode
        if chester.mode=="2":
            chester.move()
            if chester.userMove == 26: #If move equals ctrl+Z undo last movement
                chester.undo()
                chester.undo()
                chester.display(False)
                continue
        #Camera/Robot mode
        elif chester.mode=="1":
            try:
                input()
                bin = get_move() #Ignores moving of computer movement
                input()
                possibles = get_move() #Get all possible movements
                moves =[]
                for move in possibles:
                    if Move.from_uci(move) in chester.board.legal_moves: #Detect if move is legal
                        moves.append(move)
                    else:
                        for p in "qnrb": #Detects coronation of pawn
                            if Move.from_uci(move+p) in chester.board.legal_moves:
                                moves.append(move+p)
                if len(moves)>1: #If there is more than one possible move
                    if "e1c1" in moves and "a1d1" in moves:
                        chester.userMove = "e1c1"                       #Detect possible castling
                    elif "e1g1" in moves and "h1f1" in moves:
                        chester.userMove = "e1g1"
                    else: #If castling is not the case, run backup
                        moves =[]
                        squares =[]
                        possibles = []
                        new_empty = run_backup()
                        for key in new_empty:
                            if new_empty[key]!=empty_squares[key]: #IF there is an empty square that was not empty before or viceversa
                                squares.append(key)
                        for fro in squares:
                            for to in squares:
                                if fro!=to: #
                                    possibles.append(fro+to) #Create list of new possible moves
                        for move in possibles:
                            if Move.from_uci(move) in chester.board.legal_moves:
                                moves.append(move)
                            else:
                                for p in "qnrb":
                                    if Move.from_uci(move+p) in chester.board.legal_moves:
                                        moves.append(move+p)
                else:
                    try:
                        chester.userMove = moves[0] #Choose the only possible move (The first place of an array of length 1 )
                    except IndexError: #No moves available
                        message("ILLEGAL MOVE")
                        continue
                empty_squares = run_backup()

            except EOFError: #Detect ctrl+Z
                chester.undo() #undo movement
                continue

        try:
            if Move.from_uci(chester.userMove) in chester.board.legal_moves:
                chester.user_move()
                chester.chester_move(player)

            else:
                message("ILLEGAL MOVE")
        except ValueError:
            print( "Please write your move in UCI form. (\"e2e4\")")

if __name__ == "__main__":
    chester = Chester()
    player = StockfishPlayer(chester.level)
    main()
