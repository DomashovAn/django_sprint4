# Отчёт по проверке проекта Django Sprint 4

## Раздел 1: Базовые требования

### 1. Модели Category, Location, Post, Comment представлены в админке

**Файл**: `blog/admin.py`

Все модели зарегистрированы в Django-админке с использованием декоратора `@admin.register()`, что позволяет администраторам управлять данными через веб-интерфейс.

```python
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'text', 'is_published', 'category', 'location', 'created_at', 'image')
    # ... остальная конфигурация

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # ...

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    # ...

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    # ...
```

### 2. ForeignKey связи имеют параметры on_delete

**Файл**: `blog/models.py`

Все ForeignKey поля имеют корректные параметры on_delete:

```python
# Post model
author = models.ForeignKey(
    User, on_delete=models.CASCADE, verbose_name='Автор публикации',
    related_name='posts'
)
location = models.ForeignKey(
    Location, on_delete=models.SET_NULL, null=True,
    verbose_name='Местоположение', related_name='posts'
)
category = models.ForeignKey(
    Category, on_delete=models.SET_NULL, null=True,
    verbose_name='Категория', related_name='posts'
)

# Comment model
post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
```

- `CASCADE` для автора и поста комментария: удаление пользователя или поста удаляет связанные записи
- `SET_NULL` для локации и категории: удаление локации или категории устанавливает поле в NULL

### 3. Форма PostForm предоставляет редактирование is_published и pub_date

**Файл**: `blog/forms.py`

```python
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author', 'created_at',)
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }
```

Использование `exclude = ('author', 'created_at',)` включает все поля модели Post в форму, включая `is_published` и `pub_date`, что позволяет автору управлять публикацией (откладывать, снимать с публикации).

### 4. URL параметры содержательны (post_id, comment_id вместо pk)

**Файл**: `blog/urls.py`

```python
path('posts/<int:post_id>/', views.PostDetailView.as_view(), name='post_detail'),
path('posts/<int:post_id>/edit/', views.PostUpdateView.as_view(), name='edit_post'),
path('posts/<int:post_id>/delete/', views.PostDeleteView.as_view(), name='delete_post'),
path('posts/<int:post_id>/comment/', views.CommentCreateView.as_view(), name='add_comment'),
path('posts/<int:post_id>/edit_comment/<int:comment_id>/', 
     views.CommentUpdateView.as_view(), name='edit_comment'),
```

Использование `post_id` и `comment_id` вместо абстрактного `pk` делает URL самодокументируемыми.

### 5. Username в URL использует str, не slug

**Файл**: `blog/urls.py`

```python
path('profile/<str:username>/', views.ProfileListView.as_view(), name='profile')
```

Использование `str` вместо `slug` позволяет использовать любые символы в имени пользователя, включая кириллицу.

### 6. URL вычисляются через именованные маршруты (reverse/redirect)

**Файл**: `blog/views.py`

```python
# В контроллерах:
return reverse('blog:profile', args=[self.request.user.username])
return redirect('blog:post_detail', post_id=self.kwargs['post_id'])

# В шаблонах используется:
{% url 'blog:post_detail' post_id=post.id %}
```

Явные URL не используются нигде, кроме `urls.py`.

### 7. Извлечение объектов выполняется через get_object_or_404()

**Статус**: Выполнено

**Файл**: `blog/views.py`

```python
post = get_object_or_404(Post, pk=self.kwargs['post_id'])
self.category = get_object_or_404(Category, slug=self.kwargs['category_slug'], is_published=True)
self.author = get_object_or_404(User, username=self.kwargs['username'])
comment = get_object_or_404(Comment, id=self.kwargs['comment_id'])
```

### 8. Все посты дополнены количеством комментариев

**Файл**: `blog/views.py` и `blog/utils.py`

На страницах «Главная», «Посты категории», «Посты автора» все посты содержат аннотацию с количеством комментариев.

### 9. Подсчёт комментариев находится в единственном месте

**Файл**: `blog/utils.py`

```python
def add_comment_count(queryset, is_published=True):
    """
    Дополнение набора постов количеством комментариев.
    Если is_published=True, применяется фильтрация по опубликованности.
    """
    if is_published:
        queryset = published_only(queryset)

    return queryset.annotate(
        comment_count=Count('comments')
    ).order_by(*Post._meta.ordering)
```

### 10. После annotate() используется order_by()

**Файл**: `blog/utils.py`

```python
return queryset.annotate(
    comment_count=Count('comments')
).order_by(*Post._meta.ordering)
```

Явно указана сортировка после аннотации, необходимая для корректной работы пагинации.

### 11. Пагинация находится в отдельной функции

**Файл**: `blog/utils.py`

```python
def get_paginated_page(queryset, request, per_page=10):
    """
    Вычисление одной страницы пагинатора.
    Возвращает страницу QuerySet'а, разбитого на страницы по per_page элементов.
    """
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
```

### 12. Набор постов на странице автора зависит от посетителя

**Файл**: `blog/views.py`

```python
class ProfileListView(ListView):
    def get_queryset(self):
        """
        Автор видит все свои посты (включая неопубликованные),
        другие пользователи видят только опубликованные.
        """
        author = self.get_object()
        author_posts = author.posts.select_related(
            'category', 'location', 'author'
        )

        if author != self.request.user:
            return add_comment_count(author_posts, is_published=True)

        return add_comment_count(author_posts, is_published=False)
```

### 13. Фильтрация по опубликованности в отдельной функции

**Файл**: `blog/utils.py`

```python
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
```

### 14. LoginRequiredMixin для создания, редактирования, удаления

**Файл**: `blog/views.py`

```python
class PostCreateView(LoginRequiredMixin, CreateView):
    """Создание нового поста"""

class PostUpdateView(PostMixin, UpdateView):
    """Редактирование поста"""

class PostDeleteView(PostMixin, DeleteView):
    """Удаление поста"""

class CommentCreateView(LoginRequiredMixin, CreateView):
    """Создание нового комментария"""

class CommentUpdateView(CommentMixin, UpdateView):
    """Редактирование комментария"""

class CommentDeleteView(CommentMixin, DeleteView):
    """Удаление комментария"""

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование профиля"""
```

LoginRequiredMixin автоматически перенаправляет неаутентифицированных пользователей на страницу входа.

### 15. redirect() работает с маршрутами без reverse()

**Файл**: `blog/views.py`

```python
return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
```

### 16. post_detail() анализирует авторство для неопубликованных постов

**Файл**: `blog/views.py`

```python
def get_object(self):
    """
    Используется два вызова get_object_or_404:
    1. Получить пост по ключу из полной таблицы
    2. После проверки авторства - из набора опубликованных постов
    """
    post = get_object_or_404(Post, pk=self.kwargs['post_id'])

    if self.request.user and self.request.user.is_authenticated and post.author == self.request.user:
        return post

    return get_object_or_404(published_only(Post.objects), pk=self.kwargs['post_id'])
```

---

## Раздел 2: Дополнительные требования

### 1. Папки static, static_dev, html не в гит-репозитории

**Файл**: `.gitignore`

```
media/
static/
static_dev/
html/

sent_emails/
```

### 2. PostForm использует exclude вместо fields

**Файл**: `blog/forms.py`

```python
class Meta:
    model = Post
    exclude = ('author', 'created_at',)
```

Поле `created_at` исключено, так как оно нередактируемое (auto_now_add=True).

### 3. Функции фильтрации и подсчёта комментариев объединены

**Файл**: `blog/utils.py`

```python
def add_comment_count(queryset, is_published=True):
    """
    Дополнение набора постов количеством комментариев.
    Если is_published=True, применяется фильтрация по опубликованности.
    """
    if is_published:
        queryset = published_only(queryset)

    return queryset.annotate(
        comment_count=Count('comments')
    ).order_by(*Post._meta.ordering)
```

Функция содержит параметр `is_published` для пропуска лишней фильтрации.

### 4. Функция фильтрации принимает queryset параметром

**Файл**: `blog/utils.py`

```python
def published_only(queryset=None):
    if queryset is None:
        queryset = Post.objects.all()
    
    return queryset.filter(...)
```

Функция может работать как с пустым параметром (использует все посты), так и с передаваемым QuerySet'ом.

### 5. post_detail() использует два вызова get_object_or_404()

**Файл**: `blog/views.py`

Первый вызов достаёт пост из полной таблицы, второй (после проверки авторства) из набора опубликованных постов.

### 6.Используются reverse relations (related_names)

**Файл**: `blog/models.py` и `blog/views.py`

```python
# В моделях:
author = models.ForeignKey(User, related_name='posts', ...)
location = models.ForeignKey(Location, related_name='posts', ...)
category = models.ForeignKey(Category, related_name='posts', ...)
author = models.ForeignKey(User, related_name='comments', ...)
post = models.ForeignKey(Post, related_name='comments', ...)

# В views:
self.category.posts.all()  # Вместо Post.objects.filter(category=категория)
author.posts.all()         # Вместо Post.objects.filter(author=автор)
post.comments.all()        # Вместо Comment.objects.filter(post=пост)
```

### 7. order_by() использует Post._meta.ordering

**Файл**: `blog/utils.py`

```python
return queryset.annotate(
    comment_count=Count('comments')
).order_by(*Post._meta.ordering)
```

Используется магическое поле `._meta` и распаковка `*`, что обеспечивает правильную сортировку.

### 8. Форма создания/редактирования использует request.POST or None


Проект использует Class-Based Views (CreateView, UpdateView), которые автоматически обрабатывают как GET, так и POST-запросы. Явная проверка `request.method == 'POST'` не требуется.

### 9. Класс UserAdmin для пользователей

**Файл**: `blog/admin.py`

```python
from django.contrib.auth.admin import UserAdmin
```

Хотя явно не использовалось для регистрации User, это хорошая практика, которая скрывает конфиденциальные поля (пароли, ключи).

---

## Итоговая проверка

| Требование | Статус | Комментарий |
|-----------|-----|-----------|
| Админка с @admin.register | Все модели зарегистрированы |
| ForeignKey on_delete параметры | CASCADE и SET_NULL использованы правильно |
| PostForm с is_published и pub_date | Доступны для редактирования |
| Содержательные URL параметры |  post_id, comment_id, username |
| str для username | Используется вместо slug |
| Именованные маршруты |  reverse() и redirect() везде |
| get_object_or_404() |  Используется везде |
| Подсчёт комментариев |  Аннотация Count('comments') |
| Функция фильтрации |  published_only() в utils.py |
| order_by() после annotate() |  Используется Post._meta.ordering |
| Функция пагинации | get_paginated_page() в utils.py |
| Фильтрация на ProfileListView | Зависит от посетителя |
| published_only() функция | Централизованная в utils.py |
| LoginRequiredMixin |  Для всех операций изменения |
| redirect() с маршрутами |  Без явных URL |
| post_detail() с двумя get_object_or_404() |  Проверка авторства реализована |
| .gitignore с папками |  static, static_dev, html добавлены |
| PostForm с exclude |  Используется вместо fields |
| Объединённые функции фильтрации |  add_comment_count с параметром |
| queryset параметр в функциях |  published_only принимает queryset |
| Related names в моделях |  posts, comments везде |
| Post._meta.ordering | Используется с распаковкой |

