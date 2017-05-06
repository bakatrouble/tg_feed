from importlib import import_module

from telebot import TeleBot, util
from voluptuous import Schema, Required, Any
from redis import Redis

from message_types import TextMessage, PhotoMessage


schema = Schema({
    Required('bot_token'): str,
    Required('plugins'): [{
        Required('name'): str,
        Required('chat_id'): Any(str, int),
        'config': dict,
    }],
    Required('config'): dict
})


class TGFeed:
    bot: TeleBot = None
    config: dict = None
    redis: Redis = None
    plugins = []


class Plugin:
    def __init__(self, name, chat_id, func, config):
        self.name = name
        self.chat_id = chat_id
        self.func = func
        self.config = config

    def __call__(self, last_id):
        return self.func(last_id, config=self.config, global_config=TGFeed.config['config'].get(self.name, {}))


def set_config(config):
    schema(config)
    TGFeed.config = config


def init(config):
    set_config(config)
    TGFeed.bot = TeleBot(TGFeed.config['bot_token'])
    TGFeed.redis = Redis()
    # register plugins
    for plugin in TGFeed.config['plugins']:
        m = import_module(f"plugins.{plugin['name']}")
        if not (hasattr(m, 'get_updates') and callable(m.get_updates)):
            raise ImportError(f'Plugin "{plugin["name"]}" has no callable "get_updates()"')
        TGFeed.plugins.append(Plugin(plugin['name'], plugin['chat_id'], m.get_updates, plugin.get('config', {})))


def send_split_text(chat_id, text):
    for chunk in util.split_string(text, 3000):
        TGFeed.bot.send_message(chat_id, chunk)


def do_work():
    for plugin in TGFeed.plugins:
        try:
            last_id, updates = plugin(TGFeed.redis.get(f'tg_feed_{plugin.name}_{plugin.chat_id}') or 0)
            TGFeed.redis.set(f'tg_feed_{plugin.name}_{plugin.chat_id}', last_id)
            for update in updates:
                if isinstance(update, TextMessage):
                    send_split_text(plugin.chat_id, update.text)
                elif isinstance(update, PhotoMessage):
                    if len(update.text) < 200:
                        TGFeed.bot.send_photo(plugin.chat_id, update.photo, update.text)
                    else:
                        TGFeed.bot.send_photo(plugin.chat_id, update.photo)
                        send_split_text(plugin.chat_id, update.text)
        except Exception as e:
            print(e)
