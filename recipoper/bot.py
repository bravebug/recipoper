#!/usr/bin/env python
import logging
import random

from config import Config
from database import DataBase
from messages import MESSAGES
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import BotCommand
import re


logging.basicConfig(level=logging.INFO)
conf = Config()
bot = Bot(token=conf.TOKEN, parse_mode="HTML")
db = DataBase(
    database_uri=conf.SQLALCHEMY_DATABASE_URI,
    echo=conf.SQLALCHEMY_DATABASE_ECHO,
)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

recipe_difficulty_level = {key: value for value, key in db.list_levels()}

# global dictionary for storing lists of recipe IDs mixed with random.shuffle
# for each user to reduce repetitions when recommending
random_recipe_ids = dict()


def get_msg(key: str) -> str:
    return MESSAGES.get(key)


BUTTON_CANCEL_TEXT = f'{get_msg("cancel_icon")} {get_msg("cancel")}'
BUTTON_OK_TEXT = f'{get_msg("successful_action_icon")} {get_msg("ok")}'
BUTTON_REMOVE_TEXT = f'{get_msg("remove_icon")} {get_msg("remove")}'
BUTTON_LIKE_TEXT = f'{get_msg("like_icon")} {get_msg("like")}'
BUTTON_NEXT_TEXT = f'{get_msg("next_recipe_icon")} {get_msg("next_recipe")}'


class NewRecipeForm(StatesGroup):
    name = State()
    ingredients = State()
    body = State()
    level_id = State()
    time = State()
    image_whether = State()
    image = State()


class SupportForm(StatesGroup):
    msg = State()


async def setup_bot_commands(dispatcher):
    bot_commands = [
        BotCommand(command="/recipe", description=get_msg("recommend_a_recipe")),
        BotCommand(command="/help", description=get_msg("help")),
        # BotCommand(command="/about", description=get_msg("about")),
    ]
    await bot.set_my_commands(bot_commands)


@dp.message_handler(lambda message: message.from_user.id in conf.ADMIN_IDS, commands=['adm'])
async def start(message: types.Message):
    await message.answer(
         f"/add {get_msg('add')}\n"
         # f"/edit {get_msg('edit')}\n"
         # f"/stat {get_msg('stat')}\n"
         # f"/export {get_msg('export')}"
    )


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals=[BUTTON_CANCEL_TEXT, 'cancel', get_msg("cancel")], ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.answer(
        get_msg('operation_canceled'),
        reply_markup=types.ReplyKeyboardRemove()
    )


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    kb = types.InlineKeyboardMarkup()
    kb.insert(types.InlineKeyboardButton(text=get_msg("start"), callback_data="next"))
    await message.answer(
        text=get_msg("start_text"),
        reply_markup=kb,
        parse_mode="html",
    )


@dp.message_handler(lambda message: message.from_user.id in conf.ADMIN_IDS, commands='help')
async def help_cmd(message: types.Message):
    await SupportForm.msg.set()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(BUTTON_CANCEL_TEXT)
    await message.answer(get_msg("support"), reply_markup=markup)


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals=[BUTTON_CANCEL_TEXT, 'cancel', get_msg("cancel")], ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.answer(
        get_msg('operation_canceled'),
        reply_markup=types.ReplyKeyboardRemove()
    )


@dp.message_handler(lambda message: message.from_user.id in conf.ADMIN_IDS, state=SupportForm.msg)
async def process_name(message: types.Message, state: FSMContext):
    for admin_id in conf.ADMIN_IDS:
        await bot.send_message(
            admin_id,
            get_msg("support_msg").format(text=message.text, user=message.from_user.username),
            parse_mode="html",
        )
    await message.answer(get_msg("thank_for_contacting"), reply_markup=types.ReplyKeyboardRemove())
    await state.finish()


@dp.message_handler(commands=['about'])
async def about(message: types.Message):
    await message.answer(get_msg('about_text'))


@dp.message_handler(lambda message: message.from_user.id in conf.ADMIN_IDS, commands='add')
async def cmd_add(message: types.Message):
    await NewRecipeForm.name.set()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(BUTTON_CANCEL_TEXT)
    await message.answer(get_msg("send_the_name_of_the_new_recipe"), reply_markup=markup)


@dp.message_handler(lambda message: message.from_user.id in conf.ADMIN_IDS, state=NewRecipeForm.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await NewRecipeForm.next()
    await message.answer(get_msg("send_the_ingredients"))


@dp.message_handler(lambda message: message.from_user.id in conf.ADMIN_IDS, state=NewRecipeForm.ingredients)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['ingredients'] = message.text
    await NewRecipeForm.next()
    await message.answer(get_msg("send_the_recipe_body"))


@dp.message_handler(lambda message: message.from_user.id in conf.ADMIN_IDS, state=NewRecipeForm.body)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['body'] = message.text
    await NewRecipeForm.next()
    await message.answer(
        get_msg("choose_the_difficulty_level_of_the_recipe"),
        reply_markup=types.ReplyKeyboardMarkup(
            [list(recipe_difficulty_level.keys()), [BUTTON_CANCEL_TEXT]],
            resize_keyboard=True,
            one_time_keyboard=True,
            selective=True,
        ),
    )


@dp.message_handler(lambda message: message.from_user.id in conf.ADMIN_IDS, state=NewRecipeForm.level_id)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            data['level_id'] = recipe_difficulty_level[message.text]
            await NewRecipeForm.next()
            await message.answer(get_msg("how_long_cooking_take"))
        except KeyError:
            await message.answer("select_difficulty_level_on_reply_keyboard")


@dp.message_handler(lambda message: message.from_user.id in conf.ADMIN_IDS, state=NewRecipeForm.time)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['time'] = int(re.sub(r'\D+', '', message.text))
    await NewRecipeForm.next()
    await message.reply(
        get_msg("add_a_photo?"),
        reply_markup=types.ReplyKeyboardMarkup(
            [
                [
                    types.KeyboardButton(text=get_msg("yes")),
                    types.KeyboardButton(text=get_msg("no")),
                ],
                [
                    types.KeyboardButton(text=BUTTON_CANCEL_TEXT)
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
            selective=True,
        ),
    )


@dp.message_handler(lambda message: message.from_user.id in conf.ADMIN_IDS, state=NewRecipeForm.image_whether)
async def process_name(message: types.Message, state: FSMContext):
    if message.text == get_msg("yes"):
        await NewRecipeForm.next()
        await message.reply(get_msg("send_an_image"))
    elif message.text == get_msg("no"):
        async with state.proxy() as data:
            db.add_recipe(
                name=data['name'],
                ingredients=data['ingredients'],
                body=data['body'],
                level_id=data['level_id'],
                time=data['time'],
            )
        await message.answer(get_msg("new_recipe_added"), reply_markup=types.ReplyKeyboardRemove())
        await state.finish()


@dp.message_handler(
    lambda message: message.from_user.id in conf.ADMIN_IDS,
    content_types=[types.ContentType.PHOTO],
    state=NewRecipeForm.image
)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        db.add_recipe(
            name=data['name'],
            ingredients=data['ingredients'],
            body=data['body'],
            level_id=data['level_id'],
            time=data['time'],
            image=message.photo[-1].file_id,
        )
    await message.answer(get_msg("new_recipe_added"), reply_markup=types.ReplyKeyboardRemove())
    await state.finish()


@dp.message_handler(commands='recipe')
async def recipe_cmd(message: types.Message):
    if not random_recipe_ids.get(message.chat.id):
        # the global dictionary was purposefully used
        random_recipe_ids[message.chat.id] = list(db.list_recipe_ids())
        random.shuffle(random_recipe_ids[message.chat.id])
    try:
        (
            id_,
            name,
            ingredients,
            body,
            level,
            time,
            image,
            shown,
            votes,
            rating,
        ) = db.get_recipe_by_id(random_recipe_ids[message.chat.id].pop())
    except IndexError:
        await message.answer(text=get_msg("database_is_empty"))
    else:
        time_range = f"{int(time * 0.85)}-{int(time * 1.1)} {get_msg('minute')}"
        recipe = get_msg("recipe_template").format(
            name=name,
            ingredients=ingredients,
            body=body,
            level=level,
            time=time_range,
            votes=votes,
            rating=rating
        )
        kb = types.InlineKeyboardMarkup(row_width=3)
        kb.insert(types.InlineKeyboardButton(text=BUTTON_LIKE_TEXT, callback_data=f"like{id_}"))
        kb.insert(types.InlineKeyboardButton(text=BUTTON_NEXT_TEXT, callback_data="next"))
        if image:
            await message.answer_photo(photo=image)
        await message.answer(
            text=recipe,
            reply_markup=kb,
            parse_mode="html",
        )


@dp.callback_query_handler()
async def callback_handler(callback: types.CallbackQuery):
    markup = callback.message.reply_markup
    for row in markup.inline_keyboard:
        for button in row:
            if button.callback_data == callback.data:
                if button.callback_data.startswith("like"):
                    db.vote_recipe_by_id(int(button.callback_data.lstrip("like")))
                if button.callback_data == "next":
                    await recipe_cmd(callback.message)
                row.remove(button)
                await callback.message.edit_reply_markup(reply_markup=markup)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=setup_bot_commands)
