import pygame
import sys
import copy
import random

# --- Game Constants ---
WIDTH, HEIGHT = 640, 640
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS
FPS = 60

# Colors for board, highlights, and check indicators
WHITE = (240, 217, 181)
BLACK = (181, 136, 99)
HIGHLIGHT = (186, 202, 68)
CHECK_COLOR = (255, 0, 0)

# Piece values for AI evaluation (used in scoring moves)
PIECE_VALUES = {'Pawn':1, 'Knight':3, 'Bishop':3, 'Rook':5, 'Queen':9, 'King':1000}

# --- Load piece images ---
IMAGES = {}
pieces = ["P", "R", "N", "B", "Q", "K"]
colors = ["w", "b"]
for color in colors:
    for piece in pieces:
        IMAGES[color + piece] = pygame.image.load(f"assets/{color}{piece}.png")
        IMAGES[color + piece] = pygame.transform.scale(IMAGES[color + piece], (SQUARE_SIZE, SQUARE_SIZE))

# Map class names to letters for images
PIECE_MAP = {'Pawn':'P','Rook':'R','Knight':'N','Bishop':'B','Queen':'Q','King':'K'}

# --- Base Piece Class ---
class Piece:
    def __init__(self, color):
        self.color = color
        self.has_moved = False
    def valid_moves(self, pos, board):
        return []

# --- Pawn ---
class Pawn(Piece):
    def valid_moves(self, pos, board):
        x, y = pos
        moves = []
        direction = -1 if self.color=="white" else 1

        # Single and double move
        if 0 <= x + direction < 8 and board[x+direction][y] is None:
            moves.append((x+direction, y))
            if not self.has_moved and board[x+2*direction][y] is None:
                moves.append((x+2*direction, y))

        # Diagonal captures
        for dy in [-1,1]:
            nx, ny = x+direction, y+dy
            if 0<=nx<8 and 0<=ny<8:
                target = board[nx][ny]
                if target and target.color != self.color:
                    moves.append((nx, ny))

        # En passant
        if hasattr(board, 'last_move') and board.last_move:
            (sx, sy), (ex, ey), piece_moved = board.last_move
            if isinstance(piece_moved, Pawn) and abs(sx-ex)==2 and ex==x:
                if ey==y+1 or ey==y-1:
                    moves.append((x+direction, ey))
        return moves

# --- Rook ---
class Rook(Piece):
    def valid_moves(self, pos, board):
        x, y = pos
        moves = []
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x+dx, y+dy
            while 0<=nx<8 and 0<=ny<8:
                target = board[nx][ny]
                if target is None:
                    moves.append((nx, ny))
                elif target.color != self.color:
                    moves.append((nx, ny))
                    break
                else:
                    break
                nx += dx
                ny += dy
        return moves

# --- Knight ---
class Knight(Piece):
    def valid_moves(self, pos, board):
        x, y = pos
        moves = []
        for dx, dy in [(2,1),(1,2),(-1,2),(-2,1),(-2,-1),(-1,-2),(1,-2),(2,-1)]:
            nx, ny = x+dx, y+dy
            if 0<=nx<8 and 0<=ny<8 and (board[nx][ny] is None or board[nx][ny].color != self.color):
                moves.append((nx, ny))
        return moves

# --- Bishop ---
class Bishop(Piece):
    def valid_moves(self, pos, board):
        x, y = pos
        moves = []
        for dx, dy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            nx, ny = x+dx, y+dy
            while 0<=nx<8 and 0<=ny<8:
                target = board[nx][ny]
                if target is None:
                    moves.append((nx, ny))
                elif target.color != self.color:
                    moves.append((nx, ny))
                    break
                else:
                    break
                nx += dx
                ny += dy
        return moves

# --- Queen ---
class Queen(Piece):
    def valid_moves(self, pos, board):
        return Rook.valid_moves(self,pos,board) + Bishop.valid_moves(self,pos,board)

# --- King ---
class King(Piece):
    def valid_moves(self, pos, board):
        x, y = pos
        moves = []
        for dx, dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nx, ny = x+dx, y+dy
            if 0<=nx<8 and 0<=ny<8 and (board[nx][ny] is None or board[nx][ny].color != self.color):
                moves.append((nx, ny))
        return moves

# --- Chess Board Class ---
class ChessBoard:
    """
    Maintains board state, turn tracking, and rules validation
    """
    def __init__(self):
        self.board = self.create_board()
        self.turn = "white"
        self.last_move = None  # Used for en passant tracking

    def create_board(self):
        board = [[None]*8 for _ in range(8)]
        for y in range(8):
            board[1][y] = Pawn("black")
            board[6][y] = Pawn("white")
        board[0][0] = board[0][7] = Rook("black")
        board[7][0] = board[7][7] = Rook("white")
        board[0][1] = board[0][6] = Knight("black")
        board[7][1] = board[7][6] = Knight("white")
        board[0][2] = board[0][5] = Bishop("black")
        board[7][2] = board[7][5] = Bishop("white")
        board[0][3] = Queen("black")
        board[7][3] = Queen("white")
        board[0][4] = King("black")
        board[7][4] = King("white")
        return board

    # Check if a color is under check
    def is_in_check(self, color):
        for x in range(8):
            for y in range(8):
                piece = self.board[x][y]
                if piece and isinstance(piece, King) and piece.color==color:
                    king_pos = (x,y)
                    break
        enemy = "black" if color=="white" else "white"
        for x in range(8):
            for y in range(8):
                p = self.board[x][y]
                if p and p.color==enemy:
                    if king_pos in p.valid_moves((x,y), self.board):
                        return True
        return False

    # Checkmate logic
    def is_checkmate(self, color):
        if not self.is_in_check(color):
            return False
        for x in range(8):
            for y in range(8):
                piece = self.board[x][y]
                if piece and piece.color==color:
                    for move in piece.valid_moves((x,y), self.board):
                        temp = copy.deepcopy(self)
                        temp.board[move[0]][move[1]] = piece
                        temp.board[x][y] = None
                        if not temp.is_in_check(color):
                            return False
        return True

    # Stalemate logic: no legal moves but not in check
    def is_stalemate(self, color):
        if self.is_in_check(color):
            return False
        moves = self.all_valid_moves(color)
        return len(moves)==0

    # Returns all legal moves for a given color
    def all_valid_moves(self, color):
        moves=[]
        for x in range(8):
            for y in range(8):
                piece=self.board[x][y]
                if piece and piece.color==color:
                    for move in piece.valid_moves((x,y), self.board):
                        temp = copy.deepcopy(self)
                        temp.board[move[0]][move[1]] = piece
                        temp.board[x][y] = None
                        if not temp.is_in_check(color):
                            moves.append(((x,y), move))
        return moves

# --- Main Game Class ---
class Game:
    """
    Handles rendering, user interaction, AI moves, and game flow
    """
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH,HEIGHT))
        pygame.display.set_caption("Python Chess")
        self.clock = pygame.time.Clock()
        self.board = ChessBoard()
        self.dragging=False
        self.selected=None
        self.running=True
        self.possible_moves=[]

    # Draw board squares and highlights
    def draw_board(self):
        for r in range(ROWS):
            for c in range(COLS):
                color = WHITE if (r+c)%2==0 else BLACK
                pygame.draw.rect(self.screen, color, (c*SQUARE_SIZE, r*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        for move in self.possible_moves:
            mx,my=move[1],move[0]
            pygame.draw.rect(self.screen, HIGHLIGHT, (mx*SQUARE_SIZE,my*SQUARE_SIZE,SQUARE_SIZE,SQUARE_SIZE))
        # Highlight kings in check
        for x in range(8):
            for y in range(8):
                p = self.board.board[x][y]
                if isinstance(p, King) and self.board.is_in_check(p.color):
                    pygame.draw.rect(self.screen, CHECK_COLOR, (y*SQUARE_SIZE,x*SQUARE_SIZE,SQUARE_SIZE,SQUARE_SIZE))

    # Draw chess pieces
    def draw_pieces(self):
        for r in range(8):
            for c in range(8):
                p = self.board.board[r][c]
                if p:
                    key = p.color[0]+PIECE_MAP[p.__class__.__name__]
                    self.screen.blit(IMAGES[key], (c*SQUARE_SIZE,r*SQUARE_SIZE))

    # Handle user drag-and-drop moves
    def handle_drag(self,event):
        if self.board.turn!="white":
            return  # Only allow player during white turn
        if self.board.is_checkmate("white") or self.board.is_stalemate("white"):
            return
        if event.type==pygame.MOUSEBUTTONDOWN:
            x,y=event.pos
            r,c=y//SQUARE_SIZE,x//SQUARE_SIZE
            piece=self.board.board[r][c]
            if piece and piece.color=="white":
                self.dragging=True
                self.selected=(r,c)
                self.possible_moves=piece.valid_moves((r,c),self.board.board)
        elif event.type==pygame.MOUSEBUTTONUP and self.dragging:
            x,y=event.pos
            r,c=y//SQUARE_SIZE,x//SQUARE_SIZE
            if (r,c) in self.possible_moves:
                piece=self.board.board[self.selected[0]][self.selected[1]]
                # Handle pawn promotion
                if isinstance(piece,Pawn) and (r==0 or r==7):
                    choice=self.promotion_menu(piece.color)
                    self.board.board[r][c]={"Q":Queen,"R":Rook,"B":Bishop,"N":Knight}[choice](piece.color)
                    self.board.board[self.selected[0]][self.selected[1]]=None
                else:
                    self.board.board[r][c]=piece
                    self.board.board[self.selected[0]][self.selected[1]]=None
                piece.has_moved=True
                self.board.last_move=(self.selected,(r,c),piece)
                self.board.turn="black"
            self.dragging=False
            self.selected=None
            self.possible_moves=[]

    # Promotion popup menu
    def promotion_menu(self,color):
        menu_width = SQUARE_SIZE*4
        menu_height=SQUARE_SIZE
        menu_x = WIDTH//2 - menu_width//2
        menu_y = HEIGHT//2 - menu_height//2
        menu_rects=[]
        promotion_classes=[Queen,Rook,Bishop,Knight]
        running=True
        choice=None
        while running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type==pygame.MOUSEBUTTONDOWN:
                    mx,my=event.pos
                    for i,rect in enumerate(menu_rects):
                        if rect.collidepoint(mx,my):
                            choice=["Q","R","B","N"][i]
                            running=False
            self.draw_board()
            self.draw_pieces()
            menu_rects=[]
            for i,cls in enumerate(promotion_classes):
                rect=pygame.Rect(menu_x+i*SQUARE_SIZE,menu_y,SQUARE_SIZE,SQUARE_SIZE)
                menu_rects.append(rect)
                key=color[0]+cls.__name__[0]
                self.screen.blit(IMAGES[key],(rect.x,rect.y))
                pygame.draw.rect(self.screen,(255,255,255),rect,2)
            pygame.display.flip()
        return choice

    # AI move: selects best scoring move based on piece values
    def ai_move(self):
        """
        AI selects the best move for black, avoiding unnecessary sacrifices.
        """
        best_score = float('-inf')
        best_move = None

        for start, end in self.board.all_valid_moves("black"):
            piece = self.board.board[start[0]][start[1]]
            if piece is None:
                continue  # Safety check

            # Opening penalty: avoid moving queen/rook repeatedly early
            opening_penalty = 0
            if not piece.has_moved and isinstance(piece, (Queen, Rook)):
                opening_penalty = -0.3

            # Create temporary board for evaluation
            temp_board = copy.deepcopy(self.board)
            temp_piece = temp_board.board[start[0]][start[1]]
            temp_board.board[end[0]][end[1]] = temp_piece
            temp_board.board[start[0]][start[1]] = None

            # Evaluate material
            score = -self.evaluate_board(temp_board)

            # Center control bonus
            if 2 <= end[0] <= 5 and 2 <= end[1] <= 5:
                score += 0.1

            # Mobility bonus
            temp_mobility = len(temp_board.all_valid_moves("black"))
            score += 0.05 * temp_mobility

            # Apply opening penalty
            score += opening_penalty

            # Risk penalty: check if this move exposes high-value piece
            risk_penalty = 0
            enemy_moves = temp_board.all_valid_moves("white")
            for _, enemy_end in enemy_moves:
                target = temp_board.board[enemy_end[0]][enemy_end[1]]
                if target and target.color == "black" and PIECE_VALUES[type(target).__name__] >= 5:
                    risk_penalty -= PIECE_VALUES[type(target).__name__] * 0.2
            score += risk_penalty

            # Update best move
            if score > best_score:
                best_score = score
                best_move = (start, end)

        # Execute the best move
        if best_move:
            s, e = best_move
            piece = self.board.board[s[0]][s[1]]
            if piece:
                self.board.board[e[0]][e[1]] = piece
                self.board.board[s[0]][s[1]] = None
                piece.has_moved = True
                self.board.last_move = (s, e, piece)
                self.board.turn = "white"

    # Simple evaluation: sums piece values
    def evaluate_board(self,board):
        total=0
        for r in board.board:
            for p in r:
                if p:
                    val=PIECE_VALUES[p.__class__.__name__]
                    total+=val if p.color=="white" else -val
        return total

    # Main game loop
    def run(self):
        while self.running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.handle_drag(event)

            # AI turn
            if self.board.turn=="black" and self.running:
                pygame.time.delay(200)
                self.ai_move()

            # Stop game on checkmate or stalemate
            if self.board.is_checkmate("white") or self.board.is_checkmate("black") or \
               self.board.is_stalemate("white") or self.board.is_stalemate("black"):
                self.running=False

            self.draw_board()
            self.draw_pieces()
            pygame.display.flip()

if __name__=="__main__":
    game=Game()
    game.run()
