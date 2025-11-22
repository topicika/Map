import os
import django
from django.conf import settings
from cartographer.Node import GraphBuilder

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "path_finder.settings")
django.setup()

LE_PATH = os.path.join(settings.BASE_DIR, "cartographer/static/buildings/LE.json")

@profile
def load_graphs(n):
    graphs = []
    for _ in range(n):
        graphs.append(GraphBuilder.from_file(LE_PATH))
    return graphs


load_graphs(1)
