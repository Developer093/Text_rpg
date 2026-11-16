"""
간단한 텍스트 RPG
실행: python text_rpg.py
"""
import random
import sys
import time


def slow_print(text, delay=0.01):
    """글자를 한 자씩 출력해서 분위기를 살린다."""
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def ask(prompt, options):
    """options 중 하나가 입력될 때까지 반복해서 묻는다."""
    while True:
        answer = input(prompt).strip()
        if answer in options:
            return answer
        print(f"  ※ {', '.join(options)} 중에서 골라주세요.")


# ──────────────────────────────── 캐릭터 ────────────────────────────────
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

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)

    def attack(self, target, guarding=False):
        damage = max(1, self.atk + random.randint(-2, 3) - target.defense)
        if random.random() < 0.1:  # 10% 치명타
            damage *= 2
            print("  ★ 치명타! ★")
        if guarding:
            damage //= 2
        target.take_damage(damage)
        print(f"  {self.name}의 공격! {target.name}에게 {damage} 데미지 "
              f"(남은 HP {target.hp}/{target.max_hp})")


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

    def gain_exp(self, amount):
        self.exp += amount
        print(f"  경험치 +{amount} ({self.exp}/{self.exp_to_next})")
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level += 1
            self.max_hp += 10
            self.atk += 3
            self.defense += 1
            self.hp = self.max_hp
            slow_print(f"  🎉 레벨 업! Lv.{self.level} "
                       f"(HP {self.max_hp}, 공격 {self.atk}, 방어 {self.defense}) — HP 전부 회복!")

    def use_potion(self):
        if self.potions == 0:
            print("  포션이 없어요!")
            return False
        heal = 25
        self.potions -= 1
        self.hp = min(self.max_hp, self.hp + heal)
        print(f"  포션을 마셨다. HP {self.hp}/{self.max_hp} (남은 포션 {self.potions}개)")
        return True

    def status(self):
        print(f"\n[{self.name}] Lv.{self.level}  HP {self.hp}/{self.max_hp}  "
              f"공격 {self.atk}  방어 {self.defense}  "
              f"EXP {self.exp}/{self.exp_to_next}  골드 {self.gold}  포션 {self.potions}")


# ──────────────────────────────── 몬스터 ────────────────────────────────
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


class Monster(Character):
    def __init__(self, name, hp, atk, defense, exp, gold):
        super().__init__(name, hp, atk, defense)
        self.exp = exp
        self.gold = gold


def random_monster(area):
    return Monster(*random.choice(MONSTERS[area]))


# ──────────────────────────────── 전투 ────────────────────────────────
def battle(player, monster, can_run=True):
    """승리하면 True, 도망치면 None, 패배하면 False"""
    slow_print(f"\n⚔️  {monster.name}이(가) 나타났다! (HP {monster.hp})")
    while player.alive and monster.alive:
        print(f"\n  {player.name} HP {player.hp}/{player.max_hp}  |  "
              f"{monster.name} HP {monster.hp}/{monster.max_hp}")
        choice = ask("  1) 공격  2) 방어  3) 포션  4) 도망 > ", ["1", "2", "3", "4"])

        guarding = False
        if choice == "1":
            player.attack(monster)
        elif choice == "2":
            guarding = True
            print("  방어 자세를 취했다! (받는 데미지 절반)")
        elif choice == "3":
            if not player.use_potion():
                continue  # 포션이 없으면 턴 소모 없음
        elif choice == "4":
            if not can_run:
                print("  도망칠 수 없다!")
            elif random.random() < 0.5:
                print("  무사히 도망쳤다!")
                return None
            else:
                print("  도망에 실패했다!")

        if monster.alive:
            monster.attack(player, guarding=guarding)

    if player.alive:
        slow_print(f"\n  {monster.name}을(를) 쓰러뜨렸다!")
        if monster.gold:
            player.gold += monster.gold
            print(f"  골드 +{monster.gold}")
        if monster.exp:
            player.gain_exp(monster.exp)
        if random.random() < 0.2:
            player.potions += 1
            print("  몬스터가 포션을 떨어뜨렸다! (+1)")
        return True
    return False


# ──────────────────────────────── 장소 ────────────────────────────────
def shop(player):
    items = {
        "1": ("포션", 15, "potion"),
        "2": ("철검 (공격 +4)", 50, "atk"),
        "3": ("가죽 갑옷 (방어 +2)", 40, "def"),
    }
    while True:
        print(f"\n🏪 상점  (보유 골드: {player.gold})")
        for key, (name, price, _) in items.items():
            print(f"  {key}) {name} — {price}G")
        print("  0) 나가기")
        choice = ask("  > ", ["0", *items.keys()])
        if choice == "0":
            return
        name, price, kind = items[choice]
        if player.gold < price:
            print("  골드가 부족해요.")
            continue
        player.gold -= price
        if kind == "potion":
            player.potions += 1
        elif kind == "atk":
            player.atk += 4
        elif kind == "def":
            player.defense += 2
        print(f"  {name}을(를) 샀다!")


def inn(player):
    cost = 10
    if player.gold < cost:
        print("\n🛏️  여관비(10G)가 부족해요.")
        return
    player.gold -= cost
    player.hp = player.max_hp
    print(f"\n🛏️  푹 쉬었다. HP가 모두 회복됐다! (-{cost}G)")


def explore(player, area):
    if area == "던전" and player.level < 3:
        print("\n  던전 입구의 기운이 너무 강하다... (Lv.3 이상 권장)")
        if ask("  그래도 들어갈까요? (y/n) > ", ["y", "n"]) == "n":
            return True
    result = battle(player, random_monster(area))
    return result is not False


def boss_fight(player):
    slow_print("\n🔥 산 정상에 오르자 땅이 흔들린다...", 0.03)
    slow_print("🐉 거대한 드래곤이 날개를 펼쳤다!", 0.03)
    if ask("  싸우시겠습니까? (y/n) > ", ["y", "n"]) == "n":
        print("  일단 물러났다.")
        return None
    return battle(player, Monster(*BOSS), can_run=False)


# ──────────────────────────────── 메인 ────────────────────────────────
def main():
    slow_print("=" * 50)
    slow_print("        ⚔️  작은 왕국의 모험  ⚔️")
    slow_print("=" * 50)
    slow_print("왕국을 위협하는 드래곤을 물리쳐 주세요, 용사여!")
    name = input("\n당신의 이름은? > ").strip() or "용사"
    player = Player(name)
    slow_print(f"\n{player.name}의 모험이 시작됩니다!")

    while True:
        player.status()
        print("\n🏘️  마을 광장")
        print("  1) 숲 탐험   2) 던전 탐험   3) 상점   4) 여관(10G)   5) 드래곤의 산   0) 종료")
        choice = ask("  어디로 갈까요? > ", ["0", "1", "2", "3", "4", "5"])

        if choice == "0":
            print("\n다음에 또 만나요!")
            break
        elif choice == "1":
            alive = explore(player, "숲")
        elif choice == "2":
            alive = explore(player, "던전")
        elif choice == "3":
            shop(player)
            alive = True
        elif choice == "4":
            inn(player)
            alive = True
        elif choice == "5":
            result = boss_fight(player)
            if result is True:
                slow_print("\n" + "=" * 50, 0.02)
                slow_print(f"🏆 {player.name}이(가) 드래곤을 물리쳤습니다!", 0.04)
                slow_print("   왕국에 평화가 찾아왔습니다. THE END", 0.04)
                slow_print("=" * 50, 0.02)
                break
            alive = result is not False

        if not alive:
            slow_print(f"\n💀 {player.name}은(는) 쓰러지고 말았다... GAME OVER", 0.04)
            break


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\n게임을 종료합니다.")
