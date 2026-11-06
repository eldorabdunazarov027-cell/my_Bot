from aiogram.fsm.state import State, StatesGroup


class AdminAuthStates(StatesGroup):
    waiting_for_password = State()


class TaskAddStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_recurrence = State()


class TaskEditStates(StatesGroup):
    waiting_for_task_id = State()
    waiting_for_field = State()
    waiting_for_value = State()


class TaskDeleteStates(StatesGroup):
    waiting_for_task_id = State()
    confirm_delete = State()


class SetReminderTimeStates(StatesGroup):
    waiting_for_task_id = State()
    waiting_for_time = State()


class ChangePasswordStates(StatesGroup):
    waiting_for_old_password = State()
    waiting_for_new_password = State()
    confirm_new_password = State()

