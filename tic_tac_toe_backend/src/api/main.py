from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body, Path
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from dotenv import load_dotenv

from .game_logic import game_manager, Player, CellOccupiedError, GameOverError, InvalidMoveError

# Load environment variables from .env file (if present)
load_dotenv()

TAGS_METADATA = [
    {
        "name": "Game",
        "description": "Endpoints for Tic Tac Toe gameplay and session management.",
    },
]

app = FastAPI(
    title="Tic Tac Toe API",
    description="A FastAPI backend for Tic Tac Toe, supporting in-memory sessions and REST endpoints.",
    version="1.0.0",
    openapi_tags=TAGS_METADATA,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Pydantic models -----------------

class CreateGameResponse(BaseModel):
    game_id: str = Field(..., description="Unique identifier for the game session")
    board: List[List[Literal["X", "O", ""]]] = Field(..., description="Current board state")
    current_turn: Player = Field(..., description="Player whose turn it is")
    state: str = Field(..., description="Game state: in_progress, draw, or win")

class MakeMoveRequest(BaseModel):
    row: int = Field(..., ge=0, le=2, description="Row index (0-2)")
    col: int = Field(..., ge=0, le=2, description="Column index (0-2)")
    player: Player = Field(..., description="Player making the move (X or O)")

class GameStateResponse(BaseModel):
    game_id: str
    board: List[List[Literal["X", "O", ""]]]
    current_turn: Player
    state: str
    winner: Optional[Player]

# ----------------- FastAPI endpoints -----------------

@app.get("/", tags=["Health"])
def health_check():
    """Health Check, returns status for service."""
    return {"message": "Healthy"}

# PUBLIC_INTERFACE
@app.post("/games", response_model=CreateGameResponse, status_code=status.HTTP_201_CREATED, tags=["Game"], summary="Create new game session")
def create_game():
    """
    Create a new Tic Tac Toe game session.

    Returns the initial state, including a unique game ID.
    """
    game = game_manager.create_game()
    return {
        "game_id": game.game_id,
        "board": [[cell if cell is not None else "" for cell in row] for row in game.board],
        "current_turn": game.current_turn,
        "state": game.state,
    }

# PUBLIC_INTERFACE
@app.post("/games/{game_id}/moves", response_model=GameStateResponse, tags=["Game"], summary="Make a move in a game session")
def make_move(
    game_id: str = Path(..., description="Game session ID"),
    move: MakeMoveRequest = Body(..., description="Move details"),
):
    """
    Make a move in a specific game session. Returns the updated game state.

    - **game_id**: Unique identifier for the game.
    - **row, col**: Board position (0-indexed).
    - **player**: X or O (must match player's current turn).
    """
    try:
        game = game_manager.make_move(game_id, move.row, move.col, move.player)
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found.")
    except CellOccupiedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidMoveError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except GameOverError as e:
        raise HTTPException(status_code=400, detail=str(e))

    d = game.to_dict()
    return {
        "game_id": d["game_id"],
        "board": d["board"],
        "current_turn": d["current_turn"],
        "state": d["state"],
        "winner": d["winner"],
    }

# PUBLIC_INTERFACE
@app.get("/games/{game_id}", response_model=GameStateResponse, tags=["Game"], summary="Get game state")
def get_game_state(game_id: str = Path(..., description="Game session ID")):
    """
    Get the current state of a Tic Tac Toe game session.

    - **game_id**: Unique identifier for the game.
    """
    try:
        state = game_manager.get_game_state(game_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found.")
    return state
