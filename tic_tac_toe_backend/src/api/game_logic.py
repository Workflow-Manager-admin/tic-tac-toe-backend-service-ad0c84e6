import uuid
from enum import Enum
from typing import Dict, Optional, List


class Player(str, Enum):
    X = "X"
    O = "O"


class GameState(str, Enum):
    IN_PROGRESS = "in_progress"
    DRAW = "draw"
    WIN = "win"


class CellOccupiedError(Exception):
    pass


class GameOverError(Exception):
    pass


class InvalidMoveError(Exception):
    pass


class Game:
    def __init__(self, game_id: str, player_x: Optional[str] = None, player_o: Optional[str] = None):
        self.game_id = game_id
        self.board: List[List[Optional[Player]]] = [[None for _ in range(3)] for _ in range(3)]
        self.current_turn: Player = Player.X
        self.state: GameState = GameState.IN_PROGRESS
        self.winner: Optional[Player] = None
        self.player_x = player_x
        self.player_o = player_o
        self.move_count = 0

    def make_move(self, row: int, col: int, player: Player):
        if self.state != GameState.IN_PROGRESS:
            raise GameOverError("Game is already over.")

        if row not in range(3) or col not in range(3):
            raise InvalidMoveError("Move is out of bounds.")

        if self.current_turn != player:
            raise InvalidMoveError(f"It's not {player}'s turn.")

        if self.board[row][col] is not None:
            raise CellOccupiedError("Cell is already occupied.")

        self.board[row][col] = player
        self.move_count += 1

        if self.check_win(player):
            self.state = GameState.WIN
            self.winner = player
        elif self.move_count == 9:
            self.state = GameState.DRAW
        else:
            self.current_turn = Player.O if player == Player.X else Player.X

    def check_win(self, player: Player) -> bool:
        b = self.board
        # Check rows, cols, diagonals
        for i in range(3):
            if all([b[i][j] == player for j in range(3)]):
                return True
            if all([b[j][i] == player for j in range(3)]):
                return True
        if all([b[i][i] == player for i in range(3)]) or all([b[i][2 - i] == player for i in range(3)]):
            return True
        return False

    def to_dict(self):
        return {
            "game_id": self.game_id,
            "board": [[cell if cell is not None else "" for cell in row] for row in self.board],
            "current_turn": self.current_turn,
            "state": self.state,
            "winner": self.winner,
        }


class GameManager:
    def __init__(self):
        self.games: Dict[str, Game] = {}

    # PUBLIC_INTERFACE
    def create_game(self, player_x: Optional[str] = None, player_o: Optional[str] = None) -> Game:
        """Creates a new Tic Tac Toe game session."""
        game_id = str(uuid.uuid4())
        game = Game(game_id, player_x, player_o)
        self.games[game_id] = game
        return game

    # PUBLIC_INTERFACE
    def get_game(self, game_id: str) -> Game:
        """Retrieves a game by its ID, or raises KeyError if not found."""
        if game_id not in self.games:
            raise KeyError("Game not found.")
        return self.games[game_id]

    # PUBLIC_INTERFACE
    def make_move(self, game_id: str, row: int, col: int, player: Player) -> Game:
        """Processes a move for the given player and position."""
        game = self.get_game(game_id)
        game.make_move(row, col, player)
        return game

    # PUBLIC_INTERFACE
    def get_game_state(self, game_id: str) -> dict:
        """Returns the current state of the specified game."""
        game = self.get_game(game_id)
        return game.to_dict()


# Global in-memory manager
game_manager = GameManager()
