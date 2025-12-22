from datetime import datetime

from django.core.paginator import Paginator
from django.db.models import Count, QuerySet

from .models import Post


def published_only(queryset=None):
    """
    Фильтрация записей из таблицы постов по опубликованности.
    Возвращает только опубликованные посты с датой публикации не превышающей текущую
    и категорией, которая также опубликована.
    """
    if queryset is None:
        queryset = Post.objects.all()

    return queryset.filter(
        is_published=True,
        pub_date__lte=datetime.now(),
        category__is_published=True
    )


def add_comment_count(queryset, is_published=True):
    """
    Дополнение набора постов количеством комментариев.
    Если is_published=True, применяется фильтрация по опубликованности.
    Возвращает QuerySet с аннотацией comment_count.
    """
    if is_published:
        queryset = published_only(queryset)

    return queryset.annotate(
        comment_count=Count('comments')
    ).order_by(*Post._meta.ordering)


def get_paginated_page(queryset, request, per_page=10):
    """
    Вычисление одной страницы пагинатора.
    Возвращает страницу QuerySet'а, разбитого на страницы по per_page элементов.
    """
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
