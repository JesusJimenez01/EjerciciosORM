import os
import django
from django.conf import settings
from django.db.models.functions import Floor

os.environ['DJANGO_SETTINGS_MODULE'] = 'sistema_gestion_restaurantes.settings'
django.setup()


from recetario_app.models import Chef, Recipe, Restaurant, RecipeStats, RestaurantConfig
from django.db.models import Count, F, ExpressionWrapper, FloatField

"""
Trabajo de Django ORM - Consultas sobre Recetas y Restaurantes
Estudiante: Jesús Jiménez Pérez
Fecha 24/02/2025
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


"""
---------------------------------------------------------------------------------------
                                RETO FINAL
---------------------------------------------------------------------------------------
"""

chefs = [
    Chef(name="Gordon Ramsay", specialty="Cocina francesa"),
    Chef(name="Massimo Bottura", specialty="Cocina italiana"),
    Chef(name="Joan Roca", specialty="Cocina española"),
    Chef(name="René Redzepi", specialty="Cocina nórdica"),
    Chef(name="Heston Blumenthal", specialty="Cocina molecular")
]

Chef.objects.bulk_create(chefs)

restaurants = [
    Restaurant(name="Hell's Kitchen", location="Londres"),
    Restaurant(name="The Savoy Grill", location="Londres"),
    Restaurant(name="Osteria Francescana", location="Módena"),
    Restaurant(name="El Celler de Can Roca", location="Girona"),
    Restaurant(name="Noma", location="Copenhague"),
    Restaurant(name="The Fat Duck", location="Bray"),
    Restaurant(name="DiverXO", location="Madrid"),
    Restaurant(name="Tickets", location="Barcelona")
]

Restaurant.objects.bulk_create(restaurants)

# Obtener chefs de la base de datos
gordon = Chef.objects.get(name="Gordon Ramsay")
massimo = Chef.objects.get(name="Massimo Bottura")
joan = Chef.objects.get(name="Joan Roca")
rene = Chef.objects.get(name="René Redzepi")
heston = Chef.objects.get(name="Heston Blumenthal")

recipes = [
    Recipe(title="Beef Wellington", preparation_time=120, chef=gordon),
    Recipe(title="Tortellini en crema de parmesano", preparation_time=90, chef=massimo),
    Recipe(title="Cordero a la brasa con hierbas", preparation_time=75, chef=joan),
    Recipe(title="Pato salvaje con bayas nórdicas", preparation_time=110, chef=rene),
    Recipe(title="Helado de huevo y beicon", preparation_time=60, chef=heston),
    Recipe(title="Tarta de chocolate con espuma de frambuesa", preparation_time=45, chef=heston),
    Recipe(title="Paella de mariscos", preparation_time=60, chef=joan),
    Recipe(title="Bacalao con musgo y hierbas", preparation_time=80, chef=rene)
]

Recipe.objects.bulk_create(recipes)

# Obtener restaurantes y recetas de la base de datos
hells_kitchen = Restaurant.objects.get(name="Hell's Kitchen")
savoy = Restaurant.objects.get(name="The Savoy Grill")
osteria = Restaurant.objects.get(name="Osteria Francescana")
celler = Restaurant.objects.get(name="El Celler de Can Roca")
noma = Restaurant.objects.get(name="Noma")
fat_duck = Restaurant.objects.get(name="The Fat Duck")
diverxo = Restaurant.objects.get(name="DiverXO")
tickets = Restaurant.objects.get(name="Tickets")

beef_wellington = Recipe.objects.get(title="Beef Wellington")
tortellini = Recipe.objects.get(title="Tortellini en crema de parmesano")
cordero = Recipe.objects.get(title="Cordero a la brasa con hierbas")
pato = Recipe.objects.get(title="Pato salvaje con bayas nórdicas")
helado = Recipe.objects.get(title="Helado de huevo y beicon")
tarta = Recipe.objects.get(title="Tarta de chocolate con espuma de frambuesa")
paella = Recipe.objects.get(title="Paella de mariscos")
bacalao = Recipe.objects.get(title="Bacalao con musgo y hierbas")

beef_wellington.restaurants.add(hells_kitchen, savoy)
tortellini.restaurants.add(osteria)
cordero.restaurants.add(celler)
pato.restaurants.add(noma)
helado.restaurants.add(fat_duck)
tarta.restaurants.add(fat_duck)
paella.restaurants.add(diverxo)
bacalao.restaurants.add(noma, tickets)

stats = [
    RecipeStats(recipe=beef_wellington, total_orders=500, positive_reviews=450),
    RecipeStats(recipe=tortellini, total_orders=300, positive_reviews=280),
    RecipeStats(recipe=cordero, total_orders=250, positive_reviews=230),
    RecipeStats(recipe=pato, total_orders=200, positive_reviews=180),
    RecipeStats(recipe=helado, total_orders=150, positive_reviews=140),
    RecipeStats(recipe=tarta, total_orders=100, positive_reviews=90),
    RecipeStats(recipe=paella, total_orders=400, positive_reviews=370),
    RecipeStats(recipe=bacalao, total_orders=220, positive_reviews=200)
]

RecipeStats.objects.bulk_create(stats)

configs = [
    RestaurantConfig(
        restaurant=hells_kitchen,
        settings={
            "opening_hours": {"weekdays": "12pm-11pm", "weekends": "10am-11pm"},
            "services": ["delivery", "takeaway", "dine-in"],
            "restricted_dishes": {"alcohol": True, "pork": False}
        }
    ),
    RestaurantConfig(
        restaurant=savoy,
        settings={
            "opening_hours": {"weekdays": "1pm-10pm", "weekends": "11am-10pm"},
            "services": ["dine-in"],
            "restricted_dishes": {"alcohol": False, "pork": False}
        }
    ),
    RestaurantConfig(
        restaurant=noma,
        settings={
            "opening_hours": {"weekdays": "5pm-11pm", "weekends": None},
            "services": ["dine-in", "private events"],
            "restricted_dishes": {"alcohol": False, "shellfish": True}
        }
    ),
    RestaurantConfig(
        restaurant=fat_duck,
        settings={
            "opening_hours": {"weekdays": "2pm-9pm", "weekends": "12pm-9pm"},
            "services": ["dine-in", "catering"],
            "restricted_dishes": {"alcohol": True, "gluten": True}
        }
    ),
]

RestaurantConfig.objects.bulk_create(configs)

"""
--------------------------------------------------
Consulta recetas específicas atravesando relaciones con chefs y restaurantes:
--------------------------------------------------
"""

# i. Encuentra todas las recetas creadas por un chef con una especialidad específica
recetas_espanolas = Recipe.objects.filter(chef__specialty="Cocina española")
for receta in recetas_espanolas:
    print(f"- {receta.title} (Chef: {receta.chef.name})")

# ii. Lista todas las recetas que están disponibles en un restaurante ubicado en "Madrid"
recetas_madrid = Recipe.objects.filter(restaurants__location="Madrid").distinct()
for receta in recetas_madrid:
    print(f"- {receta.title}")

# iii. Encuentra todas las recetas de un chef llamado "Gordon Ramsay" que están en el restaurante "Hell's Kitchen"
""" Se debe cumplir que nombre del chef y el nombre del restaurante sean los correctos """
recetas_gordon_hk = Recipe.objects.filter(chef__name="Gordon Ramsay", restaurants__name="Hell's Kitchen").distinct()
for receta in recetas_gordon_hk:
    print(f"- {receta.title}")

# iv. Lista todos los chefs que tienen al menos una receta en un restaurante en "Barcelona"
""" Busco la location del restaurante de la receta y si hay recetas que tengan un restaurante en Barcelona me devuelve el resultado """
chefs_barcelona = Chef.objects.filter(recipe__restaurants__location="Barcelona").distinct()
for chef in chefs_barcelona:
    print(f"- {chef.name} (Especialidad: {chef.specialty})")

# v. Encuentra todas las recetas que tardan menos de 30 minutos en preparación y están disponibles en un restaurante llamado "The Savoy Grill".
""" tiempo de preparaación <30 y nombre del restaurante The Savoy Grill"""
recetas_rapidas_savoy = Recipe.objects.filter(preparation_time__lt=30, restaurants__name="The Savoy Grill").distinct()
for receta in recetas_rapidas_savoy:
    print(f"- {receta.title} ({receta.preparation_time} min)")

# vi. Obtén todas las recetas disponibles en restaurantes que tienen más de 5 recetas.
""" Primero creo con el annotate añado una cuenta del número de recetas asociadas a cada restaurante y luego filtro que haya >5 recetas, 
luego busco las recetas relacionadas con esos restaurantes """
restaurantes_populares = Restaurant.objects.annotate(num_recetas=Count('recipe')).filter(num_recetas__gt=5)
recetas_en_populares = Recipe.objects.filter(restaurants__in=restaurantes_populares).distinct()

"""
--------------------------------------------------
Usa F Expressions para actualizar dinámicamente las estadísticas de las recetas.
--------------------------------------------------
"""

# i. Incrementa el número de pedidos totales en 10 para todas las recetas
pedidos_antes = list(RecipeStats.objects.values('recipe__title', 'total_orders'))

""" Sumo 10 al total de pedidos """
RecipeStats.objects.update(total_orders=F('total_orders') + 10)

pedidos_despues = list(RecipeStats.objects.values('recipe__title', 'total_orders'))

for antes in pedidos_antes:
    print(f"- {antes['recipe__title']} ({antes['total_orders']})")

for despues in pedidos_despues:
    print(f"- {despues['recipe__title']} ({despues['total_orders']})")

# ii. Incrementa el número de opiniones positivas en un 5% (redondeando hacia abajo)
""" Uso Floor para redondear hacia abajo"""
RecipeStats.objects.update(positive_reviews=F('positive_reviews') + Floor(F('positive_reviews') * 0.05))

# iii. Calcula y anota el porcentaje de opiniones positivas para cada receta
""" Utilizo annotate para crear un campo en el modelo Recipe, que se obtiene directamente del campo positive_reviews. 
Luego, se filtran las recetas cuya cantidad de reseñas positivas sea mayor que el total de pedidos """
Recipe.objects.annotate(positive_reviews=F("recipestats__positive_reviews")).filter(positive_reviews__gt=F("recipestats__total_orders"))

# iv. Encuentra recetas que tienen más opiniones positivas que pedidos totales (datos inconsistentes)
""" Esta consulta utiliza annotate para crear un campo en el modelo Recipe, que se obtiene directamente del campo positive_reviews. 
Luego, se filtran las recetas cuya cantidad de reseñas positivas sea mayor que el total de pedidos. """
Recipe.objects.annotate(positive_reviews=F("recipestats__positive_reviews")).filter(positive_reviews__gt=F("recipestats__total_orders"))

# v. Duplica el número de pedidos totales para todas las recetas con más de 100 pedidos actualmente
""" Esta consulta filtra los registros de RecipeStats donde el campo total_orders es mayor que 100. 
Luego, utiliza update para actualizar el campo total_orders de esos registros, multiplicando su valor por 2, gracias al uso de la función F. """
RecipeStats.objects.filter(total_orders__gt=100).update(total_orders=F("total_orders") * 2)

# vi. Resetea el número de pedidos totales y opiniones positivas para recetas que no tienen pedidos registrados
""" Esta consulta filtra los registros de RecipeStats donde el campo total_orders es menor que 1. 
Luego, usa update para establecer el valor de los campos total_orders y positive_reviews a 0. """
RecipeStats.objects.filter(total_orders__lt=1).update(total_orders=0, positive_reviews=0)

"""
--------------------------------------------------
Filtra configuraciones avanzadas en el campo JSONField para encontrar horarios o servicios específicos.para encontrar horarios o servicios específicos.
--------------------------------------------------
"""

# i. Encuentra configuraciones de restaurantes que ofrecen servicio de "delivery"
RestaurantConfig.objects.filter(settings__services__icontains="delivery")

# ii. Filtra configuraciones donde los horarios de fin de semana comiencen a las "10am"
RestaurantConfig.objects.filter(settings__opening_hours__weekends__istartswith="10am")

# iii. Obtén configuraciones donde los platos con alcohol estén restringidos
RestaurantConfig.objects.filter(settings__restricted_dishes__alcohol=True)

# iv. Encuentra configuraciones que tengan más de dos servicios habilitados (como "delivery", "takeaway", etc.)
""" Utilizo el método annotate para agregar un campo calculado a los registros de RestaurantConfig. 
El campo servicios_contador se establece igual al valor de settings__services. 
Luego, se filtran los resultados para aquellos en los que servicios_contador sea mayor que 2."""
RestaurantConfig.objects.annotate(servicios_contador=F("settings__services")).filter(servicios_contador__gt=2)

# v. Filtra restaurantes que tengan horarios de apertura entre semana que incluyan "8am-10pm"
RestaurantConfig.objects.filter(settings__opening_hours__weekdays__icontains="8am-10pm")

# vi. Encuentra configuraciones donde el restaurante esté cerrado los fines de semana
RestaurantConfig.objects.filter(settings__opening_hours__weekends=None)

# vii. Consulta configuraciones que ofrezcan servicios específicos como "internet gratuito" en la sección de servicios personalizados
RestaurantConfig.objects.filter(settings__services__icontains="internet gratuito")

# viii. Encuentra configuraciones donde exista una sección restringida para "platos exclusivos" (clave dinámica)
RestaurantConfig.objects.filter(settings__icontains="platos exclusivos")