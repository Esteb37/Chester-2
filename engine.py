class StockfishPlayer(object):
    def __init__(self,level):
        self._engine = uci.popen_engine('engine\Windows\stockfish_10_x64.exe')
        self._engine.uci()
        self.level = level

    def select_move(self, board):
        self._engine.position(board)
        result = self._engine.go(movetime=self.level)
        return result.bestmove

if __name__=="engine":
    from chess import uci
