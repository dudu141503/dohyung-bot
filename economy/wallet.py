import random
import json
from datetime import datetime, timedelta

class Wallet:
    def __init__(self):
        self.balances = {}
        self.daily_bonus = 100
        self.last_bonus_claim = {}

    def create_user(self, user_id):
        if user_id not in self.balances:
            self.balances[user_id] = 0
            return True
        return False

    def add_balance(self, user_id, amount):
        if user_id in self.balances:
            self.balances[user_id] += amount
            return True
        return False

    def deduct_balance(self, user_id, amount):
        if user_id in self.balances and self.balances[user_id] >= amount:
            self.balances[user_id] -= amount
            return True
        return False

    def claim_daily_bonus(self, user_id):
        today = datetime.utcnow().date()
        if user_id not in self.last_bonus_claim:
            self.last_bonus_claim[user_id] = today - timedelta(days=1)

        if self.last_bonus_claim[user_id] < today:
            self.add_balance(user_id, self.daily_bonus)
            self.last_bonus_claim[user_id] = today
            return True
        return False

    def transfer(self, from_user, to_user, amount):
        if self.deduct_balance(from_user, amount):
            self.add_balance(to_user, amount)
            return True
        return False

    def get_balance(self, user_id):
        return self.balances.get(user_id, 0)

    def get_all_balances(self):
        return self.balances

    def save_to_file(self, filename):
        with open(filename, 'w') as f:
            json.dump({'balances': self.balances, 'last_bonus_claim': self.last_bonus_claim}, f)

    def load_from_file(self, filename):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.balances = data.get('balances', {})
                self.last_bonus_claim = data.get('last_bonus_claim', {})
        except FileNotFoundError:
            print("File not found. Starting with empty balances.")
