class BotStorage():
  bots = {}

  def add_bot(self, bot_id, bot_instance):
    self.bots[bot_id] = bot_instance

  def get_bot(self, bot_id):
    return self.bots[bot_id]
  
botStorage = BotStorage()