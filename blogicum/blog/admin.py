from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Category, Location, Post, Comment, User

admin.site.empty_value_display = 'Не задано'

TEXT = 'Если нужно скрыть публикацию, снимите галочку.'


class PostInline(admin.TabularInline):
    model = Post
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'text',
        'is_published',
        'category',
        'location',
        'created_at',
        'image',
    )
    list_editable = (
        'is_published',
        'category',
        'location',
    )
    search_fields = ('title',)
    list_filter = ('category',)
    list_display_links = ('title',)
    fieldsets = (
        ('Блок-1', {
            'fields': ('title', 'author', 'is_published',),
            'description': '%s' % TEXT,
        }),
        ('Доп. информация', {
            'classes': ('wide', 'extrapretty'),
            'fields': ('text', 'category', 'location', 'pub_date', 'image',),
        }),
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    inlines = (
        PostInline,
    )
    list_display = (
        'name',
        'is_published',
    )
    list_filter = ('name',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'text',
        'author',
        'post',
        'created_at',
    )
    list_filter = ('author',)
    list_editable = ('post',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'created_at')
    list_editable = ('is_published',)
    list_filter = ('is_published',)
    search_fields = ('title', 'description')
