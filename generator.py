import csv
import random
import copy
from tabulate import tabulate
import datetime
import os

# Вимога 1: Структури даних для груп, викладачів, предметів та аудиторій
class Auditorium:
    def __init__(self, auditorium_id, capacity):
        self.id = auditorium_id
        self.capacity = int(capacity)

class Group:
    def __init__(self, group_number, student_amount, subgroups):
        self.number = group_number
        self.size = int(student_amount)
        self.subgroups = subgroups.split(';') if subgroups else []

class Lecturer:
    def __init__(self, lecturer_id, name, subjects_can_teach, types_can_teach, max_hours_per_week):
        self.id = lecturer_id
        self.name = name
        self.subjects_can_teach = subjects_can_teach.split(';') if subjects_can_teach else []
        self.types_can_teach = types_can_teach.split(';') if types_can_teach else []
        self.max_hours_per_week = int(max_hours_per_week)
        self.assigned_hours = 0

class Subject:
    def __init__(self, subject_id, name, group_id, num_lectures, num_practicals, requires_subgroups, week_type):
        self.id = subject_id
        self.name = name
        self.group_id = group_id
        self.num_lectures = int(num_lectures)
        self.num_practicals = int(num_practicals)
        self.requires_subgroups = requires_subgroups.lower() == 'yes'
        self.week_type = week_type.lower()

# Вимога 6: Функція для читання CSV-файлів з відповідністю полів та рандомізацією даних
def read_csv(filename, cls, field_mapping):
    items = []
    if not os.path.exists(filename):
        return items
    try:
        with open(filename, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                try:
                    kwargs = {param_name: row[field_name] for field_name, param_name in field_mapping}
                    items.append(cls(**kwargs))
                except (ValueError, KeyError) as e:
                    print(f"Помилка в {filename}, рядок {reader.line_num}: {e}")
    except Exception as e:
        print(f"Помилка при читанні {filename}: {e}")
    return items

# Завантаження даних
auditoriums = read_csv(
    'auditoriums.csv',
    Auditorium,
    [('auditoriumID', 'auditorium_id'), ('capacity', 'capacity')]
)
groups = read_csv(
    'groups.csv',
    Group,
    [('groupNumber', 'group_number'), ('studentAmount', 'student_amount'), ('subgroups', 'subgroups')]
)
lecturers = read_csv(
    'lecturers.csv',
    Lecturer,
    [('lecturerID', 'lecturer_id'), ('lecturerName', 'name'), ('subjectsCanTeach', 'subjects_can_teach'),
     ('typesCanTeach', 'types_can_teach'), ('maxHoursPerWeek', 'max_hours_per_week')]
)
subjects = read_csv(
    'subjects.csv',
    Subject,
    [('id', 'subject_id'), ('name', 'name'), ('groupID', 'group_id'), ('numLectures', 'num_lectures'),
     ('numPracticals', 'num_practicals'), ('requiresSubgroups', 'requires_subgroups'), ('weekType', 'week_type')]
)

# Рандомізація даних, якщо файли порожні (Вимога 6)
if not auditoriums:
    for i in range(5):
        auditorium_id = f"A{i+1}"
        capacity = random.randint(30, 100)
        auditoriums.append(Auditorium(auditorium_id, capacity))

if not groups:
    for i in range(4):
        group_number = f"G{i+1}"
        student_amount = random.randint(20, 60)
        subgroups = "1;2" if random.choice([True, False]) else ""
        groups.append(Group(group_number, student_amount, subgroups))

if not lecturers:
    for i in range(6):
        lecturer_id = f"L{i+1}"
        name = f"Викладач {i+1}"
        subjects_can_teach = ";".join([f"S{random.randint(1, 4)}" for _ in range(2)])
        types_can_teach = "Лекція;Практика"
        max_hours_per_week = random.randint(10, 20)
        lecturers.append(Lecturer(lecturer_id, name, subjects_can_teach, types_can_teach, max_hours_per_week))

if not subjects:
    for i in range(4):
        subject_id = f"S{i+1}"
        name = f"Предмет {i+1}"
        group_id = random.choice(groups).number
        num_lectures = random.randint(5, 10)
        num_practicals = random.randint(5, 10)
        requires_subgroups = random.choice(['yes', 'no'])
        week_type = random.choice(['even', 'odd', 'both'])
        subjects.append(Subject(subject_id, name, group_id, num_lectures, num_practicals, requires_subgroups, week_type))

# Валідація даних
valid_group_ids = set(group.number for group in groups)
subjects = [subject for subject in subjects if subject.group_id in valid_group_ids]
subject_ids = set(subject.id for subject in subjects)
lecturer_subjects = set()
for lecturer in lecturers:
    lecturer_subjects.update(lecturer.subjects_can_teach)
missing_subjects = subject_ids - lecturer_subjects
if missing_subjects:
    print(f"Увага: Немає викладачів для предметів: {', '.join(missing_subjects)}")

# Визначення часових слотів (Вимога 5)
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
PERIODS = ['1', '2', '3', '4']
TIME_SLOTS = [(day, period) for day in DAYS for period in PERIODS]

class Lesson:
    def __init__(self, subject, lesson_type, group, subgroup=None):
        self.subject = subject
        self.type = lesson_type
        self.group = group
        self.subgroup = subgroup
        self.time_slot = None
        self.auditorium = None
        self.lecturer = None

# Клас розкладу з розрахунком фітнесу (Вимоги 4 і 7)
class Schedule:
    def __init__(self):
        self.timetable = {time_slot: [] for time_slot in TIME_SLOTS}
        self.fitness = None
        self.gap_penalty_weight = 1
        self.overload_penalty_weight = 2
        self.subject_penalty_weight = 1

    def calculate_fitness(self):
        penalty = 0
        # Мінімізація прогалин для груп та викладачів
        for entity in groups + lecturers:
            schedule_list = []
            entity_id = entity.number if isinstance(entity, Group) else entity.id
            for time_slot, lessons in self.timetable.items():
                for lesson in lessons:
                    if (isinstance(entity, Group) and lesson.group.number == entity_id) or \
                       (isinstance(entity, Lecturer) and lesson.lecturer and lesson.lecturer.id == entity_id):
                        schedule_list.append(time_slot)
            schedule_sorted = sorted(schedule_list, key=lambda x: (DAYS.index(x[0]), int(x[1])))
            for i in range(len(schedule_sorted) - 1):
                day1, period1 = schedule_sorted[i]
                day2, period2 = schedule_sorted[i + 1]
                if day1 == day2:
                    gaps = int(period2) - int(period1) - 1
                    penalty += self.gap_penalty_weight * max(gaps, 0)
        # Навантаження викладачів
        for lecturer in lecturers:
            hours_assigned = sum(
                1 for lessons in self.timetable.values()
                for lesson in lessons if lesson.lecturer and lesson.lecturer.id == lecturer.id
            )
            if hours_assigned > lecturer.max_hours_per_week:
                penalty += self.overload_penalty_weight * (hours_assigned - lecturer.max_hours_per_week)
        # Години по предметах
        for subject in subjects:
            scheduled_lectures = sum(
                1 for lessons in self.timetable.values()
                for lesson in lessons if lesson.subject.id == subject.id and lesson.type == 'Лекція'
            )
            scheduled_practicals = sum(
                1 for lessons in self.timetable.values()
                for lesson in lessons if lesson.subject.id == subject.id and lesson.type == 'Практика'
            )
            penalty += self.subject_penalty_weight * (abs(scheduled_lectures - subject.num_lectures) +
                                                      abs(scheduled_practicals - subject.num_practicals))
        self.fitness = 1 / (1 + penalty)

# Функція для отримання можливих викладачів для заняття (Вимога 3)
def get_possible_lecturers(lesson):
    return [
        lecturer for lecturer in lecturers
        if lesson.subject.id in lecturer.subjects_can_teach
        and lesson.type in lecturer.types_can_teach
        and lecturer.assigned_hours < lecturer.max_hours_per_week
    ]

# Функція перевірки конфліктів (Вимога 3)
def is_conflict(lesson, time_slot, schedule):
    for existing_lesson in schedule.timetable[time_slot]:
        # Перевірка викладача
        if lesson.lecturer and existing_lesson.lecturer and existing_lesson.lecturer.id == lesson.lecturer.id:
            return True
        # Перевірка групи
        if existing_lesson.group.number == lesson.group.number:
            if lesson.subgroup and existing_lesson.subgroup and existing_lesson.subgroup == lesson.subgroup:
                return True
            elif not lesson.subgroup and not existing_lesson.subgroup:
                return True
        # Перевірка аудиторії
        if lesson.auditorium and existing_lesson.auditorium and existing_lesson.auditorium.id == lesson.auditorium.id:
            if lesson.type == 'Лекція' and existing_lesson.type == 'Лекція' and lesson.lecturer == existing_lesson.lecturer:
                continue
            else:
                return True
    return False

# Призначення занять випадково без порушення жорстких обмежень (Вимога 3)
def assign_randomly(lesson, schedule):
    available_time_slots = TIME_SLOTS.copy()
    random.shuffle(available_time_slots)
    for time_slot in available_time_slots:
        week_type = lesson.subject.week_type
        week_number = random.randint(1, 14)
        if week_type != 'both':
            if (week_type == 'even' and week_number % 2 != 0) or \
               (week_type == 'odd' and week_number % 2 == 0):
                continue
        if not is_conflict(lesson, time_slot, schedule):
            lesson.time_slot = time_slot
            schedule.timetable[time_slot].append(lesson)
            return True
    return False

# Створення початкової популяції (Вимога 6)
def create_initial_population(pop_size):
    population = []
    for _ in range(pop_size):
        schedule = Schedule()
        for subject in subjects:
            group = next((g for g in groups if g.number == subject.group_id), None)
            if not group:
                continue
            # Лекції
            for _ in range(subject.num_lectures):
                lesson = Lesson(subject, 'Лекція', group)
                possible_lecturers = get_possible_lecturers(lesson)
                if not possible_lecturers:
                    continue
                lesson.lecturer = random.choice(possible_lecturers)
                lesson.lecturer.assigned_hours += 1
                suitable_auditoriums = [aud for aud in auditoriums if aud.capacity >= group.size]
                if not suitable_auditoriums:
                    lesson.lecturer.assigned_hours -= 1
                    continue
                lesson.auditorium = random.choice(suitable_auditoriums)
                if not assign_randomly(lesson, schedule):
                    lesson.lecturer.assigned_hours -= 1
            # Практичні заняття
            practicals = subject.num_practicals
            subgroups = group.subgroups if subject.requires_subgroups else [None]
            for subgroup in subgroups:
                num_practicals = practicals // len(subgroups)
                for _ in range(num_practicals):
                    lesson = Lesson(subject, 'Практика', group, subgroup)
                    possible_lecturers = get_possible_lecturers(lesson)
                    if not possible_lecturers:
                        continue
                    lesson.lecturer = random.choice(possible_lecturers)
                    lesson.lecturer.assigned_hours += 1
                    subgroup_size = group.size // len(subgroups) if subgroup else group.size
                    suitable_auditoriums = [aud for aud in auditoriums if aud.capacity >= subgroup_size]
                    if not suitable_auditoriums:
                        lesson.lecturer.assigned_hours -= 1
                        continue
                    lesson.auditorium = random.choice(suitable_auditoriums)
                    if not assign_randomly(lesson, schedule):
                        lesson.lecturer.assigned_hours -= 1
        schedule.calculate_fitness()
        population.append(schedule)
    return population

# Функція селекції (Вимога 6)
def selection(population):
    population.sort(key=lambda x: x.fitness, reverse=True)
    survivors = population[:len(population) // 2]
    return survivors

# Функція кросоверу (Вимога 6)
def crossover(parent1, parent2):
    child = Schedule()
    for time_slot in TIME_SLOTS:
        lessons = parent1.timetable[time_slot] if random.random() < 0.5 else parent2.timetable[time_slot]
        for lesson in lessons:
            if not is_conflict(lesson, time_slot, child):
                child.timetable[time_slot].append(copy.deepcopy(lesson))
    child.calculate_fitness()
    return child

# Розширена функція мутації (Бонусний пункт 8)
def mutate(schedule):
    mutation_type = random.choice(['time_slot', 'lecturer', 'auditorium'])
    for _ in range(5):
        time_slot = random.choice(TIME_SLOTS)
        if schedule.timetable[time_slot]:
            lesson = random.choice(schedule.timetable[time_slot])
            if mutation_type == 'time_slot':
                new_time_slot = random.choice(TIME_SLOTS)
                if new_time_slot == lesson.time_slot:
                    continue
                week_type = lesson.subject.week_type
                week_number = random.randint(1, 14)
                if week_type != 'both':
                    if (week_type == 'even' and week_number % 2 != 0) or \
                       (week_type == 'odd' and week_number % 2 == 0):
                        continue
                if not is_conflict(lesson, new_time_slot, schedule):
                    schedule.timetable[lesson.time_slot].remove(lesson)
                    lesson.time_slot = new_time_slot
                    schedule.timetable[new_time_slot].append(lesson)
            elif mutation_type == 'lecturer':
                possible_lecturers = get_possible_lecturers(lesson)
                if possible_lecturers:
                    lesson.lecturer = random.choice(possible_lecturers)
            elif mutation_type == 'auditorium':
                suitable_auditoriums = [aud for aud in auditoriums if aud.capacity >= lesson.group.size]
                if suitable_auditoriums:
                    lesson.auditorium = random.choice(suitable_auditoriums)
    schedule.calculate_fitness()

# Реалізація генетичного алгоритму (Вимога 6 та Бонусні пункти 4, 5, 6)
def genetic_algorithm(pop_size, generations):
    population = create_initial_population(pop_size)
    best_schedule = max(population, key=lambda x: x.fitness)
    for generation in range(generations):
        selected = selection(population)
        new_population = []
        while len(new_population) < pop_size:
            if random.random() < 0.1:
                new_individual = create_initial_population(1)[0]
                new_population.append(new_individual)
                continue
            parent1, parent2 = random.sample(selected, 2)
            child = crossover(parent1, parent2)
            if random.random() < 0.7:
                mutate(child)
            else:
                if child.fitness < min(parent1.fitness, parent2.fitness):
                    continue
            new_population.append(child)
        population = new_population
        current_best = max(population, key=lambda x: x.fitness)
        if current_best.fitness > best_schedule.fitness:
            best_schedule = current_best
        if (generation + 1) % 10 == 0 or best_schedule.fitness == 1.0:
            print(f'Покоління {generation + 1}: Найкращий фітнес = {best_schedule.fitness}')
        if best_schedule.fitness == 1.0:
            break
    return best_schedule

# Функція виведення розкладу (Вимога 7)
def print_schedule(schedule):
    even_week_table = []
    odd_week_table = []
    headers = ['Часовий слот', 'Група(и)', 'Предмет', 'Тип', 'Викладач', 'Аудиторія', 'Студенти', 'Місткість']
    for time_slot in TIME_SLOTS:
        lessons = schedule.timetable[time_slot]
        for lesson in lessons:
            weeks = ['EVEN', 'ODD'] if lesson.subject.week_type == 'both' else [lesson.subject.week_type.upper()]
            timeslot_str = f"{time_slot[0]}, період {time_slot[1]}"
            group_str = lesson.group.number + (f" (Підгрупа {lesson.subgroup})" if lesson.subgroup else "")
            lecturer_str = lesson.lecturer.name if lesson.lecturer else "N/A"
            auditorium_str = lesson.auditorium.id if lesson.auditorium else "N/A"
            students = lesson.group.size // len(lesson.group.subgroups) if lesson.subgroup else lesson.group.size
            row = [timeslot_str, group_str, lesson.subject.name, lesson.type, lecturer_str, auditorium_str,
                   str(students), str(lesson.auditorium.capacity)]
            if 'EVEN' in weeks:
                even_week_table.append(row)
            if 'ODD' in weeks:
                odd_week_table.append(row)
    print("\nНайкращий розклад - ПАРНИЙ тиждень:\n")
    print(tabulate(even_week_table, headers=headers, tablefmt="grid", stralign="center") if even_week_table else "Немає занять для ПАРНОГО тижня.\n")
    print("\nНайкращий розклад - НЕПАРНИЙ тиждень:\n")
    print(tabulate(odd_week_table, headers=headers, tablefmt="grid", stralign="center") if odd_week_table else "Немає занять для НЕПАРНОГО тижня.\n")

# Запуск генетичного алгоритму та виведення фінального розкладу
best_schedule = genetic_algorithm(pop_size=50, generations=100)
print_schedule(best_schedule)
