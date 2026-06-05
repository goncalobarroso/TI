from pygrabber.dshow_graph import FilterGraph

def get_cameras():
    graph = FilterGraph()
    devices = graph.get_input_devices()
    
    if not devices:
        print("Windows is reporting ZERO cameras to Python.")
        return
        
    print("--- Windows Camera Device Map ---")
    for index, device_name in enumerate(devices):
        print(f"Index: {index} | Name: {device_name}")

get_cameras()