"""
작은 왕국의 모험 - GUI 버전 (tkinter)
실행: python text_rpg_gui.py
※ tkinter는 파이썬에 기본 포함되어 있어 따로 설치할 필요가 없습니다.
"""
import random
import tkinter as tk
from tkinter import messagebox, simpledialog

# ════════════════════════════════════════════════════════════════
#  1. 게임 데이터
# ════════════════════════════════════════════════════════════════
# 이름, HP, 공격, 방어, 경험치, 골드
MONSTERS = {
    "숲": [
        ("슬라임", 15, 4, 0, 8, 5),
        ("들쥐", 12, 5, 1, 7, 4),
        ("고블린", 22, 6, 1, 12, 10),
    ],
    "던전": [
        ("해골 병사", 35, 10, 3, 20, 15),
        ("오크", 45, 12, 4, 28, 20),
        ("어둠 마법사", 30, 15, 2, 25, 25),
    ],
}
BOSS = ("드래곤", 120, 18, 6, 0, 0)

# 키, 이름, 가격, 종류
SHOP_ITEMS = [
    ("potion", "포션", 15),
    ("atk", "철검 (공격+4)", 50),
    ("def", "가죽 갑옷 (방어+2)", 40),
]
INN_COST = 10
POTION_HEAL = 25


# ════════════════════════════════════════════════════════════════
#  2. 캐릭터
# ════════════════════════════════════════════════════════════════
class Character:
    def __init__(self, name, hp, atk, defense):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.defense = defense

    @property
    def alive(self):
        return self.hp > 0


class Player(Character):
    def __init__(self, name):
        super().__init__(name, hp=40, atk=8, defense=2)
        self.level = 1
        self.exp = 0
        self.gold = 20
        self.potions = 2

    @property
    def exp_to_next(self):
        return self.level * 20


class Monster(Character):
    def __init__(self, name, hp, atk, defense, exp, gold):
        super().__init__(name, hp, atk, defense)
        self.exp = exp
        self.gold = gold


# ════════════════════════════════════════════════════════════════
#  3. 게임 로직 (화면과 분리 — 메시지는 out() 콜백으로 내보냄)
# ════════════════════════════════════════════════════════════════
class Game:
    """mode: town / battle / shop / gameover / ending"""

    def __init__(self, out):
        self.out = out          # out(text, tag) 형태의 함수
        self.player = None
        self.monster = None
        self.can_run = True
        self.mode = "town"

    # ── 시작 ──
    def start(self, name):
        self.player = Player(name)
        self.mode = "town"
        self.out("════════════════════════════════", "title")
        self.out("      ⚔  작은 왕국의 모험  ⚔", "title")
        self.out("════════════════════════════════", "title")
        self.out("왕국을 위협하는 드래곤을 물리쳐 주세요!", "info")
        self.out(f"{name}의 모험이 시작됩니다.\n", "info")

    # ── 마을 ──
    def explore(self, area):
        self.start_battle(Monster(*random.choice(MONSTERS[area])), can_run=True)

    def boss(self):
        self.out("\n산 정상에 오르자 땅이 흔들린다...", "enemy")
        self.out("거대한 드래곤이 날개를 펼쳤다!", "enemy")
        self.start_battle(Monster(*BOSS), can_run=False)

    def inn(self):
        p = self.player
        if p.gold < INN_COST:
            self.out(f"여관비({INN_COST}G)가 부족해요.", "warn")
            return
        p.gold -= INN_COST
        p.hp = p.max_hp
        self.out(f"푹 쉬었다. HP가 모두 회복됐다! (-{INN_COST}G)", "heal")

    # ── 상점 ──
    def open_shop(self):
        self.mode = "shop"
        self.out("\n[상점] 어서 오세요!", "gold")

    def buy(self, key):
        p = self.player
        name, price = next((n, pr) for k, n, pr in SHOP_ITEMS if k == key)
        if p.gold < price:
            self.out("골드가 부족해요.", "warn")
            return
        p.gold -= price
        if key == "potion":
            p.potions += 1
        elif key == "atk":
            p.atk += 4
        elif key == "def":
            p.defense += 2
        self.out(f"{name}을(를) 샀다! (-{price}G)", "gold")

    def leave_shop(self):
        self.mode = "town"
        self.out("마을 광장으로 돌아왔다.", "info")

    # ── 전투 ──
    def start_battle(self, monster, can_run):
        self.monster = monster
        self.can_run = can_run
        self.mode = "battle"
        self.out(f"\n⚔ {monster.name}이(가) 나타났다! (HP {monster.hp})", "enemy")

    def _hit(self, attacker, target, guarding=False):
        damage = max(1, attacker.atk + random.randint(-2, 3) - target.defense)
        crit = random.random() < 0.1
        if crit:
            damage *= 2
        if guarding:
            damage //= 2
        target.hp = max(0, target.hp - damage)
        tag = "dmg" if attacker is self.player else "enemy"
        prefix = "★치명타! " if crit else ""
        self.out(f"{prefix}{attacker.name}의 공격! {target.name}에게 {damage} 데미지", tag)

    def act(self, action):
        """전투 중 플레이어 행동: attack / guard / potion / run"""
        p, m = self.player, self.monster
        guarding = False

        if action == "attack":
            self._hit(p, m)
        elif action == "guard":
            guarding = True
            self.out("방어 자세! 받는 데미지 절반", "info")
        elif action == "potion":
            if p.potions == 0:
                self.out("포션이 없어요!", "warn")
                return  # 턴 소모 없음
            p.potions -= 1
            p.hp = min(p.max_hp, p.hp + POTION_HEAL)
            self.out(f"포션을 마셨다. HP {p.hp}/{p.max_hp}", "heal")
        elif action == "run":
            if not self.can_run:
                self.out("도망칠 수 없다!", "warn")
            elif random.random() < 0.5:
                self.out("무사히 도망쳤다!", "info")
                self.monster = None
                self.mode = "town"
                return
            else:
                self.out("도망에 실패했다!", "warn")

        if m.alive:
            self._hit(m, p, guarding)
        self._check_battle_end()

    def _check_battle_end(self):
        p, m = self.player, self.monster
        if not p.alive:
            self.out(f"\n{p.name}은(는) 쓰러지고 말았다... GAME OVER", "enemy")
            self.mode = "gameover"
            return
        if m.alive:
            return

        self.out(f"{m.name}을(를) 쓰러뜨렸다!", "gold")
        if m.name == BOSS[0]:
            self.out("\n════════════════════════════════", "title")
            self.out(f"  {p.name}이(가) 드래곤을 물리쳤습니다!", "title")
            self.out("  왕국에 평화가 찾아왔습니다. THE END", "title")
            self.out("════════════════════════════════", "title")
            self.mode = "ending"
            return
        p.gold += m.gold
        self.out(f"골드 +{m.gold}", "gold")
        self._gain_exp(m.exp)
        if random.random() < 0.2:
            p.potions += 1
            self.out("몬스터가 포션을 떨어뜨렸다! (+1)", "heal")
        self.monster = None
        self.mode = "town"

    def _gain_exp(self, amount):
        p = self.player
        p.exp += amount
        self.out(f"경험치 +{amount}", "info")
        while p.exp >= p.exp_to_next:
            p.exp -= p.exp_to_next
            p.level += 1
            p.max_hp += 10
            p.atk += 3
            p.defense += 1
            p.hp = p.max_hp
            self.out(f"★ 레벨 업! Lv.{p.level} — HP 전부 회복! ★", "level")


# ════════════════════════════════════════════════════════════════
#  4. 화면 (tkinter)
# ════════════════════════════════════════════════════════════════
BG = "#1e1e2e"
PANEL = "#2a2a3d"
FG = "#e0e0e0"
FONT = ("Malgun Gothic", 11)
FONT_BOLD = ("Malgun Gothic", 11, "bold")
FONT_BIG = ("Malgun Gothic", 14, "bold")

TAG_COLORS = {
    "title": "#f5c542",
    "info": "#cfcfcf",
    "dmg": "#7ec8ff",
    "enemy": "#ff7a7a",
    "heal": "#7dff9a",
    "gold": "#ffd36e",
    "level": "#d58bff",
    "warn": "#ffa94d",
}


class HPBar(tk.Canvas):
    def __init__(self, master, width=220, height=18):
        super().__init__(master, width=width, height=height, bg="#444",
                         highlightthickness=0)
        self.w, self.h = width, height

    def set(self, hp, max_hp):
        self.delete("all")
        ratio = hp / max_hp if max_hp else 0
        color = "#4cd964" if ratio > 0.5 else "#ffcc00" if ratio > 0.25 else "#ff3b30"
        self.create_rectangle(0, 0, self.w * ratio, self.h, fill=color, width=0)
        self.create_text(self.w / 2, self.h / 2, text=f"{hp} / {max_hp}",
                         fill="white", font=("Malgun Gothic", 9, "bold"))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("작은 왕국의 모험")
        self.geometry("820x560")
        self.minsize(700, 480)
        self.configure(bg=BG)

        self.game = Game(self.log)
        self._build_layout()

        name = simpledialog.askstring("모험의 시작", "당신의 이름은?", parent=self)
        self.game.start((name or "").strip() or "용사")
        self.refresh()

    # ── 레이아웃 ──
    def _build_layout(self):
        # 왼쪽: 상태창
        left = tk.Frame(self, bg=PANEL, padx=14, pady=14)
        left.pack(side="left", fill="y")

        self.lbl_name = tk.Label(left, font=FONT_BIG, bg=PANEL, fg="#f5c542")
        self.lbl_name.pack(anchor="w")
        tk.Label(left, text="HP", font=FONT_BOLD, bg=PANEL, fg=FG).pack(anchor="w", pady=(10, 0))
        self.hp_bar = HPBar(left)
        self.hp_bar.pack(anchor="w")
        tk.Label(left, text="EXP", font=FONT_BOLD, bg=PANEL, fg=FG).pack(anchor="w", pady=(8, 0))
        self.exp_bar = tk.Canvas(left, width=220, height=8, bg="#444", highlightthickness=0)
        self.exp_bar.pack(anchor="w")

        self.lbl_stats = tk.Label(left, font=FONT, bg=PANEL, fg=FG, justify="left")
        self.lbl_stats.pack(anchor="w", pady=(12, 0))

        # 적 정보 (전투 중에만 표시)
        self.enemy_frame = tk.Frame(left, bg=PANEL)
        tk.Label(self.enemy_frame, text="─────── VS ───────", bg=PANEL,
                 fg="#888", font=FONT).pack(pady=(20, 6))
        self.lbl_enemy = tk.Label(self.enemy_frame, font=FONT_BIG, bg=PANEL, fg="#ff7a7a")
        self.lbl_enemy.pack(anchor="w")
        self.enemy_bar = HPBar(self.enemy_frame)
        self.enemy_bar.pack(anchor="w", pady=(4, 0))

        # 오른쪽: 로그 + 버튼
        right = tk.Frame(self, bg=BG, padx=10, pady=10)
        right.pack(side="left", fill="both", expand=True)

        self.lbl_place = tk.Label(right, font=FONT_BIG, bg=BG, fg=FG, anchor="w")
        self.lbl_place.pack(fill="x")

        log_frame = tk.Frame(right, bg=BG)
        log_frame.pack(fill="both", expand=True, pady=8)
        scroll = tk.Scrollbar(log_frame)
        scroll.pack(side="right", fill="y")
        self.txt = tk.Text(log_frame, bg="#151520", fg=FG, font=FONT, wrap="word",
                           relief="flat", padx=10, pady=8, yscrollcommand=scroll.set,
                           state="disabled")
        self.txt.pack(side="left", fill="both", expand=True)
        scroll.config(command=self.txt.yview)
        for tag, color in TAG_COLORS.items():
            self.txt.tag_config(tag, foreground=color)
        self.txt.tag_config("title", font=FONT_BOLD)
        self.txt.tag_config("level", font=FONT_BOLD)

        self.btn_frame = tk.Frame(right, bg=BG)
        self.btn_frame.pack(fill="x")

    # ── 로그 출력 ──
    def log(self, text, tag="info"):
        self.txt.config(state="normal")
        self.txt.insert("end", text + "\n", tag)
        self.txt.see("end")
        self.txt.config(state="disabled")

    # ── 버튼 ──
    def _set_buttons(self, buttons):
        for w in self.btn_frame.winfo_children():
            w.destroy()
        cols = 3
        for i, (label, cmd, color) in enumerate(buttons):
            b = tk.Button(self.btn_frame, text=label, command=cmd, font=FONT_BOLD,
                          bg=color, fg="white", activebackground=color,
                          activeforeground="white", relief="flat", cursor="hand2",
                          pady=8)
            b.grid(row=i // cols, column=i % cols, sticky="ew", padx=3, pady=3)
        for c in range(cols):
            self.btn_frame.columnconfigure(c, weight=1)

    def do(self, func, *args):
        """게임 함수 실행 후 화면 갱신"""
        func(*args)
        self.refresh()

    # ── 화면 갱신 ──
    def refresh(self):
        g, p = self.game, self.game.player

        self.lbl_name.config(text=f"{p.name}  Lv.{p.level}")
        self.hp_bar.set(p.hp, p.max_hp)
        self.exp_bar.delete("all")
        self.exp_bar.create_rectangle(0, 0, 220 * p.exp / p.exp_to_next, 8,
                                      fill="#9b6bff", width=0)
        self.lbl_stats.config(text=(
            f"공격력   {p.atk}\n"
            f"방어력   {p.defense}\n"
            f"골드     {p.gold} G\n"
            f"포션     {p.potions} 개\n"
            f"EXP      {p.exp} / {p.exp_to_next}"))

        if g.mode == "battle":
            self.enemy_frame.pack(anchor="w", fill="x")
            self.lbl_enemy.config(text=g.monster.name)
            self.enemy_bar.set(g.monster.hp, g.monster.max_hp)
        else:
            self.enemy_frame.pack_forget()

        if g.mode == "town":
            self.lbl_place.config(text="■ 마을 광장")
            self._set_buttons([
                ("숲 탐험", lambda: self.do(g.explore, "숲"), "#3a7d44"),
                ("던전 탐험", self.enter_dungeon, "#5a4a8a"),
                ("드래곤의 산", self.enter_boss, "#a33b3b"),
                ("상점", lambda: self.do(g.open_shop), "#b5832a"),
                (f"여관 ({INN_COST}G)", lambda: self.do(g.inn), "#2f6f8f"),
                ("종료", self.destroy, "#555"),
            ])
        elif g.mode == "battle":
            self.lbl_place.config(text=f"■ 전투 — {g.monster.name}")
            self._set_buttons([
                ("공격", lambda: self.do(g.act, "attack"), "#c0392b"),
                ("방어", lambda: self.do(g.act, "guard"), "#2c6fa8"),
                (f"포션 ({p.potions})", lambda: self.do(g.act, "potion"), "#27ae60"),
                ("도망", lambda: self.do(g.act, "run"),
                 "#555" if not g.can_run else "#7f8c8d"),
            ])
        elif g.mode == "shop":
            self.lbl_place.config(text=f"■ 상점  (보유 {p.gold}G)")
            buttons = [(f"{name}\n{price}G", lambda k=key: self.do(g.buy, k), "#b5832a")
                       for key, name, price in SHOP_ITEMS]
            buttons.append(("나가기", lambda: self.do(g.leave_shop), "#555"))
            self._set_buttons(buttons)
        elif g.mode in ("gameover", "ending"):
            self.lbl_place.config(text="■ GAME OVER" if g.mode == "gameover" else "■ THE END")
            self._set_buttons([
                ("다시 시작", self.restart, "#3a7d44"),
                ("종료", self.destroy, "#555"),
            ])

    # ── 확인 창이 필요한 행동 ──
    def enter_dungeon(self):
        if self.game.player.level < 3 and not messagebox.askyesno(
                "경고", "던전의 기운이 너무 강하다... (Lv.3 이상 권장)\n그래도 들어갈까요?"):
            return
        self.do(self.game.explore, "던전")

    def enter_boss(self):
        if messagebox.askyesno("드래곤의 산", "드래곤과 싸우시겠습니까?\n(보스전에서는 도망칠 수 없습니다)"):
            self.do(self.game.boss)

    def restart(self):
        self.txt.config(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.config(state="disabled")
        self.game.start(self.game.player.name)
        self.refresh()


if __name__ == "__main__":
    App().mainloop()
