from ETS2LA.Handlers import plugins
from ETS2LA.UI import *
import psutil

class Page(ETS2LAPage):

    url = "/stats"
    refresh_rate = 5
    
    # Key is the .exe name without the extension, value is the description.
    descriptions = {
        "trucksbook": "Trucksbook will invalidate any jobs you do while having ETS2LA running / the SDK installed."
    }
    
    def is_unsupported_software_running(self) -> list[str]:
        execs = self.descriptions.keys()
        found = []
        for p in psutil.process_iter():
            for app in execs:
                try:
                    if app in p.name():
                        found.append(app)
                except psutil.NoSuchProcess:
                    pass # Usually indicates that a process has exited
            
        return found
    
    def get_all_python_process_mem_usage_percent(self):
        total = 0
        python = 0
        node = 0
        for proc in psutil.process_iter():
            try:
                if "python" in proc.name().lower(): # backend
                    total += proc.memory_percent()
                    python += proc.memory_percent()
                if "node" in proc.name().lower():   # frontend
                    total += proc.memory_percent()
                    node += proc.memory_percent()
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return total, [python, node]
    
    def get_all_plugin_mem_usage_percent(self):
        by_plugin = {}
        pids = plugins.get_all_process_pids()
        for key, value in pids.items():
            by_plugin[key] = 0
            try:
                proc = psutil.Process(value)
                by_plugin[key] = proc.memory_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return by_plugin
    
    def render(self):
        unsupported = self.is_unsupported_software_running()
        if unsupported:
            with Container(styles.FlexHorizontal() + styles.Style(
                    classname="w-full border rounded-lg justify-center shadow-md",
                    height="2.2rem",
                    background="#321b1b",
                    padding="0 4px 0 0",
                    gap="4px"
                )):
                with Tooltip() as t:
                    with t.trigger:
                        Text("Conflicting software!", style=styles.Style(
                            classname="text-xs text-red-500 default"
                        ))
                    with t.content:
                        for app in unsupported:
                            Text(f"{app}", style=styles.Classname("text-xs"))
                            Text(f"{self.descriptions.get(app, 'No description available')}", style=styles.Classname("text-xs") + styles.Description())
        else:
            with Container(styles.FlexHorizontal() + 
                        styles.Classname("w-full border rounded-lg justify-center shadow-md") + 
                        styles.Height("2.2rem") +
                        styles.Padding("0 4px 0 0") +
                        styles.Gap("4px")):
                
                content_style = styles.Style()
                content_style.background = "#1e1e1e"
                content_style.padding = "2px"
                content_style.classname = "border"
                with Tooltip() as t:
                    with t.trigger:
                        Text(f"RAM: {round(psutil.virtual_memory().percent, 1)}%", style=styles.Description() + styles.Classname("text-xs"))
                    with t.content as c:
                        c.style = content_style
                        Markdown(f"```\n{round(psutil.virtual_memory().used / 1024 ** 3, 1)} GB / {round(psutil.virtual_memory().total / 1024 ** 3, 1)} GB\n```")
                        
                process_mem, per_type = self.get_all_python_process_mem_usage_percent()
                tooltip_text = f"```\n┏ Python: {round(per_type[0] * psutil.virtual_memory().total / 100 / 1024 ** 3,1)} GB\n"
                try:
                    for key, value in self.get_all_plugin_mem_usage_percent().items():
                        tooltip_text += f"┃  {key}: {round(value * psutil.virtual_memory().total / 100 / 1024 ** 3,1)} GB\n"
                except: pass
                if per_type[1] > 0:
                    tooltip_text += "┃\n"
                    tooltip_text += f"┣ Node: {round(per_type[1] * psutil.virtual_memory().total / 100 / 1024 ** 3,1)} GB\n"
                    
                tooltip_text += "┃\n"
                tooltip_text += f"┗ Total: {round(process_mem * psutil.virtual_memory().total / 100 / 1024 ** 3,1)} GB\n```"
                
                with Tooltip() as t:
                    with t.trigger:
                        Text(f"<- {round(process_mem, 1)}% ETS2LA", style=styles.Description() + styles.Classname("text-xs"))
                    with t.content as c:
                        c.style = content_style
                        Markdown(tooltip_text)