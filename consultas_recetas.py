import os
import django
from django.conf import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'sistema_gestion_restaurantes.settings'
django.setup()


from recetario_app.models import Chef, Recipe, Restaurant, RecipeStats, RestaurantConfig
from django.db.models import Count, F, ExpressionWrapper, FloatField

"""
Trabajo de Django ORM - Consultas sobre Recetas y Restaurantes
Estudiante: Jesús Jiménez Pérez
Fecha Febrero - 2025
"""

"""
-------------------------------------------------------------------------------------------------
1. Saving ForeignKey y ManyToManyField Fields
Objetivo: Trabajar con relaciones entre modelos al guardar datos.
-------------------------------------------------------------------------------------------------
"""

# 1.1 Crea un chef llamado "Gordon Ramsay" con la especialidad "Cocina francesa".
chef = Chef.objects.create(name="Gordon Ramsay", specialty="Cocina francesa")

# 1.2 Crea una receta llamada "Beef Wellington" con un tiempo de preparación de 120 minutos, creada por "Gordon Ramsay".
receta = Recipe.objects.create(title="Beef Wellington", preparation_time=120, chef=chef)

# 1.3 Añade esta receta a dos restaurantes: "Hell's Kitchen" en Londres y "The Savoy Grill" también en Londres.
""" Primero creo ambos restaurantes y luego uso add para asignar la receta a los restaurantes """
hells_kitchen = Restaurant.objects.create(name="Hell's Kitchen", location="Londres")
savoy_grill = Restaurant.objects.create(name="Savoy Grill", location="Londres")

receta.restaurants.add(hells_kitchen, savoy_grill)

"""
-------------------------------------------------------------------------------------------------
2. QuerySets are Lazy
Objetivo: Entender la evaluación perezosa de los QuerySets.
-------------------------------------------------------------------------------------------------
"""

# 2.1 Crea un QuerySet para filtrar recetas que contengan la palabra "Beef" en el título.
recipes = Recipe.objects.filter(title__icontains="Beef")
"""
¿Se ejecuta la consulta en este momento?
No, simplemente se crea el QuerySet pero no se ejecuta
"""

# 2.2 Convierte el QuerySet en una lista y observa cuándo se ejecuta:
recipes_list = list(recipes) # Siguiendo el debug aquí se ejecuta el QuerySet

# 2.3 Modifica el QuerySet para ordenar los resultados por tiempo de preparación. ¿El QuerySet inicial se ejecuta otra vez?
recipes = recipes.order_by('preparation_time')
""" No, se crea un nuevo QuerySet pero no se ejecuta ya que no es necesario, esto se puede ver en el DEBUG, ya que el valor de recipes es: 
SELECT "recetario_app_recipe"."id", "recetario_app_recipe"."title", "recetario_app_recipe"."preparation_time", "recetario_app_recipe"."chef_id" FROM "recetario_app_recipe" WHERE "recetario_app_recipe"."title" LIKE %Beef% ESCAPE '\' ORDER BY "recetario_app_recipe"."preparation_time" ASC 
"""

""" 
-------------------------------------------------------------------------------------------------
3. Field Lookups
Objetivo: Practicar diferentes tipos de lookups.
-------------------------------------------------------------------------------------------------
"""

# 3.1 Encuentra recetas cuyo tiempo de preparación esté entre 30 y 90 minutos.
""" Uso gte y lte para que sea >=30 y <=90"""
recipes_30_90 = Recipe.objects.filter(preparation_time__gte=30, preparation_time__lte=90)

# 3.2 Busca recetas cuyo título comience con "Chocolate".
""" Filtro las recetas cuyo nombre comienza con 'Chocolate' """
chocolate_recipes = Recipe.objects.filter(title__startswith="Chocolate")

# 3.3 Excluye recetas creadas por chefs con especialidad en "Cocina francesa".
""" Aqui hago una consulta que atraviesa la relación entre modelos para poder excluir la especialidad del chef """
france_sucks = Recipe.objects.exclude(chef__specialty="Cocina francesa")

"""
-------------------------------------------------------------------------------------------------
4. Lookups that Span Relationships
Objetivo: Realizar consultas que atraviesen relaciones entre modelos.
-------------------------------------------------------------------------------------------------
"""

# 4.1 Encuentra todas las recetas disponibles en restaurantes ubicados en Londres.
""" Filtro por el campo location del restaurante de la receta y uso distinct para evitar duplicados"""
recipes_londres = Recipe.objects.filter(restaurants__location="Londres").distinct()

# 4.2 Lista los chefs que tienen al menos una receta disponible en "Hell's Kitchen".
""" Busco que en el campo nombre del restaurante de la receta del chef esté 'Hell's Kitchen' y uso distinct para evitar duplicados"""
hells_kitchen_chefs = Chef.objects.filter(recipe__restaurants__name="Hell's Kitchen").distinct()

# 4.3 Filtra restaurantes que tienen más de 5 recetas en su menú.
""" Uso annotate para obtener los restaurantes con un conteo de sus recetas y filtro para obtener los que tengan >5 recetas"""
restaurantes_muchas_recetas = Restaurant.objects.annotate(recipe_count=Count('recipe')).filter(recipe_count__gt=5)

"""
-------------------------------------------------------------------------------------------------
5. F Expressions
Objetivo: Usar F Expressions para realizar cálculos o comparaciones entre campos.
-------------------------------------------------------------------------------------------------
"""

# 5.1 Filtra recetas que tienen más opiniones positivas que pedidos totales (un caso improbable para comprobar lógica).
""" Uso gt para que sea > y la F expression para comparar con el campo total_orders """
recetas_muy_positivas = RecipeStats.objects.filter(positive_reviews__gt=F('total_orders'))

# 5.2 Incrementa el número de pedidos totales para todas las recetas en 10.
""" Uso update para actualizar el campo deseado (en este caso total_orders) uso una F expression para obtener el valor de total_orders y le sumo 10 """
RecipeStats.objects.update(total_orders=F('total_orders') + 10)

# 5.3 Calcula el porcentaje de opiniones positivas para cada receta.
""" He usado ExpressionWrapper porque quiero que el resultado se guarde como Float para que el resultado semuestre correctamente,
además he multiplicado primero para que los valores se conviertan a Float ya que positive_review y total_orders son enteros. 
Si divido primero y luego multiplico por 100 daría un resultado incorrecto """
porcentajes_opiniones_positivas = RecipeStats.objects.annotate(positive_percentage=ExpressionWrapper(F('positive_reviews') * 100.0 / F('total_orders'),output_field=FloatField()))

"""
-------------------------------------------------------------------------------------------------
6. Querying JSONField
Objetivo: Trabajar con consultas en campos JSONField.
-------------------------------------------------------------------------------------------------
"""

# 6.1 Inserta una configuración para "Hell's Kitchen" con el siguiente JSON:
""" Creo un RestaurantConfig con los campos que pide el enunciado"""
config = RestaurantConfig.objects.create(
    restaurant=Restaurant.objects.get(name="Hell's Kitchen"),
    settings={
    "opening_hours": {"weekdays": "12pm-11pm", "weekends": "10am-11pm"},
    "services": ["delivery", "takeaway", "dine-in"],
    "restricted_dishes": {"alcohol": True, "pork": False} # True y False estaban en minúsculas en el enunciado 🤓☝️
    }
)
print(RestaurantConfig.objects.all().count())

# 6.2 Filtra configuraciones donde el servicio "delivery" esté disponible.
""" Filtro las RestaurenteConfigs cuyo campo services de settings contienen delivery """
delivery_disponible = RestaurantConfig.objects.filter(settings__services__contains="delivery")

# 6.3 Encuentra configuraciones donde los platos con alcohol estén restringidos.
""" Filtro el campo settings de RestaurantCofig para que restricted_dishes sea True """
sin_alcohol = RestaurantConfig.objects.filter(settings__restricted_dishes__alcohol=True)

# 6.4 Consulta configuraciones con horarios de fin de semana que comiencen a las "10am"
""" Filtro para que weekends de opening_hours de settings empiece por '10am' """
horarios_am = RestaurantConfig.objects.filter(settings__opening_hours__weekends__startswith="10am")

# 6.5 Encuentra configuraciones que ofrezcan más de dos servicios.
""" En sqlite no funciona __len así que he probado a buscar que el indice 2 de settings no esté vacío lo que significaría que hay más de 2 servicios y me funciona.
__len debería funcionar con Postgres """
# varios_servicios = RestaurantConfig.objects.filter(settings__services__len__gt=2)

varios_servicios = RestaurantConfig.objects.filter(settings__services__2__isnull=False)
