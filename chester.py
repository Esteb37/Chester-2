#Chester Adaptive Robotic Chess Player
#Author: Esteban Padilla Cerdio
#Version: 2.5

#------------------------Libraries--------------------------



#Create player entity from external applicaton




#--------------------Chess game functions---------------------

class Chester():

    #Detect special cases
    def __init__(self):
        self.level = int(input("Level: "))*100 #Transforms level to max search time in milliseconds
        self.mode = input("Mode (1: robot, 2: digital): ")
        self.board = Board()

    def check_detect(self):
        if self.board.is_checkmate():
            message("CHECKMATE")
        elif self.board.is_stalemate():
            message("STALEMATE")
        elif self.board.is_check():
            message("CHECK")

    def user_move(self):
        self.board.push(Move.from_uci(self.userMove))
        self.display(False)
        self.check_detect()


    def chester_move(self,player):
        self.board.push(player.select_move(self.board))
        self.display(False)
        self.check_detect()

    def display(self,moving):
        return display_board(self.board,moving)

    def undo(self):
        self.board.pop()

    def move(self):
        self.userMove = self.display(True)

if __name__ == "chester":
    from vision import message,display_board
    from chess import Move, Board
