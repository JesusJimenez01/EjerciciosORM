from django.contrib import admin

from recetario_app.models import Chef, Recipe, Restaurant

admin.site.register(Chef)
admin.site.register(Recipe)
admin.site.register(Restaurant)
