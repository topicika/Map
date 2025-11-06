
from django.http import JsonResponse
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.template import loader
from django.shortcuts import render
from urllib.parse import urlencode
from .Node import *
import os
import threading

_graph_cache = {}
_graph_lock = threading.Lock()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "static/buildings")

BUILDING_LEVELS = {
    "LE.json": {
        "levels": [-1, 0, 1, 2, 3, 4, 5, 6, 7],
        "images": ["LE-1.png", "LE0.png", "LE1.png", "LE2.png", "LE3.png", "LE4.png", "LE5.png", "LE6.png", "LE7.png"]
    }
}


def load_all_graphs():
    if _graph_cache:
        return _graph_cache

    with _graph_lock:
        if not _graph_cache:
            for filename in os.listdir(DATA_PATH):
                if filename.endswith(".json"):
                    filepath = os.path.join(DATA_PATH, filename)
                    try:
                        _graph_cache[filename] = GraphBuilder.from_file(filepath)
                        print(f"Loaded graph: {filename}")
                    except Exception as e:
                        print(f"Failed to load {filename}: {e}")
    return _graph_cache


def index(request):
    return render(request, 'result.html')


def map_result(request):
    map_names = ["LE.json"]
    template = loader.get_template('proba_result.html')
    source = request.GET.get("sourceinput", "")
    goal = request.GET.get("goalinput", "")
    dataset = request.GET.get("dataset", "LE.json")
    avoid_stairs = request.GET.get("avoidstairs", False) == "on"
    use_closed = request.GET.get("useclosed", False) == "on"
    use_astar = request.GET.get("useastar", False) == "on"

    if dataset not in map_names:
        dataset = "LE.json"

    query_params = {
        "dataset": dataset,
        "sourceinput": source,
        "goalinput": goal,
        "avoidstairs": "on" if avoid_stairs else "",
        "useclosed": "on" if use_closed else "",
        "useastar": "on" if use_astar else "",
    }

    if source == "" or goal == "":
        messages.error(request, "Az indulási hely vagy az úti cél nincs kitöltve!")
        return redirect("/?" + urlencode(query_params))

    algorithm_name = ""
    if use_astar:
        algorithm_name = "astar"
    else:
        algorithm_name = "dijkstra"

    load_all_graphs()
    graph = _graph_cache.get(dataset)
    path = PathFinder.find_path(
        graph=graph,
        source_id=source,
        goal_id=goal,
        accessible=avoid_stairs,
        use_closed_corridors=use_closed,
        algorithm=algorithm_name,
    )

    if path == False:
        messages.error(request, "Az indulási hely vagy cél nem megfelelő azonosítót tartalmaz!")
        return redirect("/?" + urlencode(query_params))

    if len(path) == 0:
        messages.error(request, "A jelenlegi beállításoknak megfelelő útvonal nem létezik!")
        return redirect("/?" + urlencode(query_params))

    context = {
        "path_json": path,
        "levels": list(zip(BUILDING_LEVELS[dataset]["levels"], BUILDING_LEVELS[dataset]["images"])),
    }

    return HttpResponse(template.render(context, request))


def search(request):
    if request.method != "GET":
        return HttpResponse(status=405)

    search_text = request.GET.get("node", "").strip()
    filename = request.GET.get("file", "LE.json")

    if not search_text:
        return JsonResponse({"nodes": []}, status=200)

    load_all_graphs()
    graph = _graph_cache.get(filename)

    if not graph:
        return HttpResponse(f"Graph not found: {filename}", status=404)

    suggestions = graph.search_for_targetables(search_text)
    dictionarydata = []
    for node in suggestions:
        dictionarydata.append({
            "identifier": node.get_identifier(),
            "aliases": list(node.get_aliases()) if isinstance(node, Targetable) else []
        })

    return JsonResponse({"nodes": dictionarydata}, status=200)


load_all_graphs()
