import pygame
import random
import sys
import time
from abc import ABC, abstractmethod
pygame.init()

# ==================== KONSTANTA ====================
WIDTH, HEIGHT = 1130, 700
GRID_SIZE, CARD_WIDTH, CARD_HEIGHT = 4, 150, 100
MARGIN, FPS = 20, 60

BACKGROUND = (40, 44, 52)
CARD_BACK = (86, 98, 246)
CARD_COLORS = [
    (255, 89, 94), (255, 202, 58), (138, 201, 38), (255, 0, 0),
    (106, 76, 147), (242, 100, 25), (0, 200, 200), (200, 0, 200)
]

# ==================== SOUND EFFECT ====================
pygame.mixer.init()
flip_sound = pygame.mixer.Sound("sound card.mp3")

# ==================== ABSTRACT CLASS ====================
class Drawable(ABC):
    @abstractmethod
    def draw(self, surface): pass
    
    @abstractmethod
    def update(self): pass

# ==================== BASE CLASS ====================
class GameObject(Drawable):
    def __init__(self, x, y, w, h):
        self._x = x
        self._y = y
        self._width = w
        self._height = h
        self._rect = pygame.Rect(x, y, w, h)
        self._visible = True
    
    def set_position(self, x, y=None):
        if y is None and isinstance(x, tuple):
            self._x, self._y = x
        else:
            self._x = x
            self._y = y
        self._rect.topleft = (self._x, self._y)
    
    def set_visible(self, visible): self._visible = visible
    def is_visible(self): return self._visible
    def draw(self, surface): pass
    def update(self): pass
    
    def is_clicked(self, pos):
        return self._rect.collidepoint(pos) and self._visible

# ==================== BUTTON CLASS ====================
class Button(GameObject):
    def __init__(self, x, y, w, h, text, action=None):
        super().__init__(x, y, w, h)
        self._text = text
        self._action = action
        self._hovered = False
        self._font = pygame.font.SysFont("Arial", 28)
    
    def draw(self, surface):
        if not self._visible: return
        
        color = (100, 160, 210) if self._hovered else (0, 0, 180)
        pygame.draw.rect(surface, color, self._rect, border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255), self._rect, 2, border_radius=8)
        
        text = self._font.render(self._text, True, (255, 255, 255))
        text_rect = text.get_rect(center=self._rect.center)
        surface.blit(text, text_rect)
    
    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self._hovered = self.is_clicked(mouse_pos)
    
    def handle_click(self, pos):
        if self.is_clicked(pos) and self._action:
            self._action()
            return True
        return False

# ==================== CARD CLASS ====================
class Card(GameObject):
    def __init__(self, x, y, value):
        super().__init__(x, y, CARD_WIDTH, CARD_HEIGHT)
        self._value = value
        self.__flipped = False
        self.__matched = False
    
    def get_value(self): return self._value
    def is_flipped(self): return self.__flipped
    def is_matched(self): return self.__matched
    
    def flip(self):
        if not self.__matched:
            self.__flipped = not self.__flipped
            # Play sound effect saat kartu dibalik
            if flip_sound:
                flip_sound.play()
            return True
        return False
    
    def set_matched(self):
        self.__matched = True
        self.__flipped = True
    
    def reset(self):
        self.__flipped = False
        self.__matched = False
    
    def update(self): pass
    
    def draw(self, surface, font=None):
        if not self._visible: return
        
        if self.__flipped or self.__matched:
            color = CARD_COLORS[self._value - 1]
            pygame.draw.rect(surface, color, self._rect, border_radius=10)
            pygame.draw.rect(surface, (255, 255, 255), self._rect, 3, border_radius=10)
            
            if font:
                text = font.render(str(self._value), True, (255, 255, 255))
                text_rect = text.get_rect(center=self._rect.center)
                surface.blit(text, text_rect)
            
            if self.__matched:
                pygame.draw.rect(surface, (0, 255, 0, 100), self._rect, 4, border_radius=10)
        else:
            pygame.draw.rect(surface, CARD_BACK, self._rect, border_radius=10)
            pygame.draw.rect(surface, (200, 200, 255), self._rect, 3, border_radius=10)
            
            pattern_rect = pygame.Rect(
                self._rect.x + 15,
                self._rect.y + 15,
                self._rect.width - 30,
                self._rect.height - 30
            )
            pygame.draw.rect(surface, (70, 80, 220), pattern_rect, border_radius=6)

# ==================== GAME MANAGER ====================
class GameManager:
    def __init__(self):
        self.game_state = {
            "total_games": 0,
            "best_time": float('inf'),
            "current_time": 0,
            "matched_pairs": 0,
            "is_running": False,
            "is_complete": False
        }
    
    def start_game(self):
        self.game_state.update({
            "current_time": 0,
            "matched_pairs": 0,
            "is_running": True,
            "is_complete": False
        })
        self.game_state["total_games"] += 1
    
    def complete_game(self, final_time):
        self.game_state["current_time"] = final_time
        self.game_state["is_running"] = False
        self.game_state["is_complete"] = True
        
        if final_time < self.game_state["best_time"]:
            self.game_state["best_time"] = final_time

# ==================== MAIN GAME ====================
class RecallFlipGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("RecallFlip - Memory Game")
        
        # fonts
        self.title_font = pygame.font.SysFont("Arial", 50, bold=True)
        self.ui_font = pygame.font.SysFont("Arial", 32)
        self.card_font = pygame.font.SysFont("Arial", 40, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 28)
        
        self.clock = pygame.time.Clock()
        
        self.game_manager = GameManager()
        self.cards = []
        
        self.first_card = None
        self.second_card = None
        self.can_click = True
        self.start_time = 0
        
        self.setup_ui()
        self.initialize_cards()
    
    def setup_ui(self): 
        btn_width, btn_height = 200, 50
        self.restart_button = Button(
            WIDTH // 2 - btn_width - 20, 
            HEIGHT - 60,
            btn_width, 
            btn_height, 
            "RESTART", 
            self.restart_game
        )
        
        self.quit_button = Button(
            WIDTH // 2 + 20, 
            HEIGHT - 60,
            btn_width, 
            btn_height, 
            "QUIT", 
            self.quit_game
        )
        
        self.restart_button.set_visible(False)
        self.quit_button.set_visible(False)
    
    def initialize_cards(self):
        total_width = GRID_SIZE * CARD_WIDTH + (GRID_SIZE - 1) * MARGIN
        total_height = GRID_SIZE * CARD_HEIGHT + (GRID_SIZE - 1) * MARGIN
        
        # Posisi kartu di tengah
        start_x = (WIDTH - total_width) // 2 + 140
        start_y = (HEIGHT - total_height) // 2 + 40
        
        values = list(range(1, 9)) * 2
        random.shuffle(values)
        
        self.cards.clear()
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = start_x + col * (CARD_WIDTH + MARGIN)
                y = start_y + row * (CARD_HEIGHT + MARGIN)
                card = Card(x, y, values[row * GRID_SIZE + col])
                self.cards.append(card)
    
    def handle_click(self, pos):
        self.restart_button.update()
        self.quit_button.update()
        
        # PERBAIKAN: Reset game state jika di state complete dan user klik kartu
        if self.game_manager.game_state["is_complete"]:
            if self.restart_button.handle_click(pos) or self.quit_button.handle_click(pos):
                return 
            
        # Jika game belum dimulai, mulai game
        if not self.game_manager.game_state["is_running"] and not self.game_manager.game_state["is_complete"]:
            self.start_time = time.time()
            self.game_manager.start_game()
        
        # informasi bila game sedang di mainkan
        if self.can_click and self.game_manager.game_state["is_running"]:
            for card in self.cards:
                if card.is_clicked(pos) and not card.is_flipped() and not card.is_matched():
                    card.flip()  #sound akan diputar
                    
                    if self.first_card is None:
                        self.first_card = card
                    else:
                        self.second_card = card
                        self.can_click = False
                        pygame.time.set_timer(pygame.USEREVENT, 800)
                    break
    
    def check_match(self):
        if self.first_card and self.second_card:
            if self.first_card.get_value() == self.second_card.get_value():
                self.first_card.set_matched()
                self.second_card.set_matched()
                self.game_manager.game_state["matched_pairs"] += 1
                
                if self.game_manager.game_state["matched_pairs"] == 8:
                    game_time = time.time() - self.start_time
                    self.game_manager.complete_game(game_time)
                    self.restart_button.set_visible(True)
                    self.quit_button.set_visible(True)
            else:
                # putar sound lagi saat kartu dibalik kembali
                self.first_card.flip()
                self.second_card.flip()
            
            self.first_card = None
            self.second_card = None
            self.can_click = True
    
    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds_remaining = seconds % 60
        return f"{minutes}:{seconds_remaining:05.2f}"
    
    def draw_header(self):
        title = self.title_font.render("RECALLFLIP", True, (255, 255, 200))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        
        pairs_text = f"Matched: {self.game_manager.game_state['matched_pairs']}/8"
        pairs_surf = self.ui_font.render(pairs_text, True, (255, 255, 255))
        self.screen.blit(pairs_surf, (WIDTH // 2 - pairs_surf.get_width() // 2, 110))
    
    def draw_sidebar_info(self):
        sidebar_x = 40
        sidebar_y = (HEIGHT - 300) // 2 + 40
        
        sidebar_bg = pygame.Rect(sidebar_x - 20, sidebar_y - 20, 280, 340)
        pygame.draw.rect(self.screen, (50, 54, 62), sidebar_bg, border_radius=10)
        pygame.draw.rect(self.screen, (86, 98, 246), sidebar_bg, 3, border_radius=10)
        
        info_title = self.ui_font.render("GAME INFO", True, (255, 215, 0))
        sidebar_center_x = sidebar_x + (280 // 2) - (info_title.get_width() // 1.5)
        self.screen.blit(info_title, (sidebar_center_x, sidebar_y))
        
        y_offset = 60
        
        if self.game_manager.game_state["is_running"]:
            current_time = time.time() - self.start_time
        else:
            current_time = self.game_manager.game_state["current_time"]
        
        time_text = f"Time: {self.format_time(current_time)}"
        time_surf = self.ui_font.render(time_text, True, (100, 200, 255))
        self.screen.blit(time_surf, (sidebar_x, sidebar_y + y_offset))
        y_offset += 50
        
        best_time = self.game_manager.game_state["best_time"]
        best_text = f"Best: {self.format_time(best_time) if best_time != float('inf') else '--:--.--'}"
        best_surf = self.ui_font.render(best_text, True, (255, 215, 0))
        self.screen.blit(best_surf, (sidebar_x, sidebar_y + y_offset))
        y_offset += 50
        
        games_text = f"Games: {self.game_manager.game_state['total_games']}"
        games_surf = self.ui_font.render(games_text, True, (200, 200, 255))
        self.screen.blit(games_surf, (sidebar_x, sidebar_y + y_offset))
        y_offset += 50
        
        if self.game_manager.game_state["is_complete"]:
            status = "Game Complete"
            color = (100, 255, 100)
        elif self.game_manager.game_state["is_running"]:
            status = "Game Running"
            color = (100, 200, 255)
        else:
            status = "Ready to Start"
            color = (255, 255, 200)
        
        status_surf = self.ui_font.render(status, True, color)
        self.screen.blit(status_surf, (sidebar_x, sidebar_y + y_offset))
    
    def draw_instructions(self):
        total_height = GRID_SIZE * CARD_HEIGHT + (GRID_SIZE - 1) * MARGIN
        start_y = (HEIGHT - total_height) // 2 + 40
        last_card_bottom = start_y + total_height
        
        instruction_y = last_card_bottom + 40
        
        if self.game_manager.game_state["is_complete"]:
            text = "Klik RESTART untuk bermain lagi atau kartu untuk mulai baru"
            color = (100, 255, 100)
        elif self.game_manager.game_state["is_running"]:
            text = "Cocokkan sepasang kartu yang sama!"
            color = (200, 220, 255)
        else:
            text = "Klik kartu apapun untuk memulai permainan!"
            color = (255, 255, 200)
        
        instr_surf = self.ui_font.render(text, True, color)
        self.screen.blit(instr_surf, (WIDTH // 2 - instr_surf.get_width() // 2, instruction_y))
    
    def draw_game_over(self):
        if not self.game_manager.game_state["is_complete"]:
            return
        
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        congrats = self.title_font.render("CONGRATULATIONS!", True, (100, 255, 100))
        self.screen.blit(congrats, (WIDTH // 2 - congrats.get_width() // 2, HEIGHT // 2 - 100))
        
        final_time = self.game_manager.game_state["current_time"]
        time_text = f"Final Time: {self.format_time(final_time)}"
        time_surf = self.ui_font.render(time_text, True, (100, 200, 255))
        self.screen.blit(time_surf, (WIDTH // 2 - time_surf.get_width() // 2, HEIGHT // 2 - 30))
        
        if final_time == self.game_manager.game_state["best_time"]:
            best_msg = self.ui_font.render("NEW BEST TIME!", True, (255, 215, 0))
            self.screen.blit(best_msg, (WIDTH // 2 - best_msg.get_width() // 2, HEIGHT // 2 + 30))
    
    def restart_game(self):
        # Reset semua kartu
        for card in self.cards:
            card.reset()
        
        # Reset variabel permainan
        self.first_card = None
        self.second_card = None
        self.can_click = True
        self.start_time = 0
        
        # Acak ulang nilai kartu
        values = list(range(1, 9)) * 2
        random.shuffle(values)
        for i, card in enumerate(self.cards):
            card._value = values[i]
        
        # PERBAIKAN PENTING: Reset game state
        self.game_manager.game_state.update({
            "current_time": 0,
            "matched_pairs": 0,
            "is_running": False,   
            "is_complete": False   
        }) 
  
        self.restart_button.set_visible(False)
        self.quit_button.set_visible(False)
 
        pygame.time.set_timer(pygame.USEREVENT, 0)
    
    def quit_game(self):
        pygame.quit()
        sys.exit()
    
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_click(event.pos)
                elif event.type == pygame.USEREVENT:
                    self.check_match()
                    pygame.time.set_timer(pygame.USEREVENT, 0)
            
            self.screen.fill(BACKGROUND)
            
            for card in self.cards:
                card.draw(self.screen, self.card_font)
            
            self.draw_header()
            self.draw_sidebar_info()
            self.draw_instructions()
            
            self.restart_button.draw(self.screen)
            self.quit_button.draw(self.screen)
            
            self.draw_game_over()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        self.quit_game()

# ==================== MAIN ====================
if __name__ == "__main__":
    print("=" * 60)
    print("RECALLFLIP - Memory Game")
    print("=" * 60)
    print("Temukan pasangan kartu yang cocok!")
    print("Suara akan diputar saat kartu dibalik")
    print("Kontrol: Klik kartu untuk bermain")
    print("=" * 60)
    
    game = RecallFlipGame()
    game.run()
 