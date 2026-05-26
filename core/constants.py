# список всех тегов
ALL_TAGS = [
    {'id': 1, 'name': 'Python'},
    {'id': 2, 'name': 'Django'},
    {'id': 3, 'name': 'JavaScript'},
    {'id': 4, 'name': 'React'},
    {'id': 5, 'name': 'Vue.js'},
    {'id': 6, 'name': 'HTML/CSS'},
    {'id': 7, 'name': 'SQL'},
    {'id': 8, 'name': 'PostgreSQL'},
    {'id': 9, 'name': 'Git'},
    {'id': 10, 'name': 'Docker'},
    {'id': 11, 'name': 'Linux'},
    {'id': 12, 'name': 'API'},
    {'id': 13, 'name': 'Machine Learning'},
    {'id': 14, 'name': 'Flask'},
    {'id': 15, 'name': 'FastAPI'},
]


# Функция для получения всех тегов
def get_all_tags():
    return ALL_TAGS


# Функция для получения тега по ID
def get_tag_by_id(tag_id):
    for tag in ALL_TAGS:
        if tag['id'] == tag_id:
            return tag
    return None


# Функция для получения тега по имени
def get_tag_by_name(tag_name):
    for tag in ALL_TAGS:
        if tag['name'].lower() == tag_name.lower():
            return tag
    return None
