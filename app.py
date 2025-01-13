"""
This file contains all the app code for the Epstein Civil Uprising Model.
"""

from mesa.visualization import Slider, SolaraViz, make_plot_component, make_space_component

from agents import Citizen, CitizenState, Cop
from model import EpsteinCivilViolence

"""
Define the colors for agent and cop visualizations
"""
COP_COLOR = "#000000"
agent_colors = {
    CitizenState.ACTIVE: "#FE6100",
    CitizenState.QUIET: "#648FFF",
    CitizenState.ARRESTED: "#808080"
}

def citizen_cop_portrayal(agent):
    """Function to define how citizens and cops appear in the solara app"""
    if agent is None:
        return
    portryal = {
        "size": 50
    }
    if isinstance(agent, Citizen):
        portryal["color"] = agent_colors[agent.state]
    elif isinstance(agent, Cop):
        portryal["color"] = COP_COLOR
    
    return portryal

def post_process(ax):
    """Function that processes the Epstein model in the solara app"""
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.get_figure().set_size_inches(10, 10)

model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "height": 40,
    "width": 40,
    "citizen_density": Slider("Initial Agent Density", 0.7, 0.0, 0.9, 0.1),
    "cop_density": Slider("Initial Cop Density", 0.04, 0.0, 0.1, 0.01),
    "citizen_vision": Slider("Citizen Vision", 7, 1, 10, 1),
    "cop_vision": Slider("Cop Vision", 7, 1, 10, 1),
    "legitimacy": Slider("Government Legitimacy", 0.82, 0.0, 1, 0.01),
    "max_jail_term": Slider("Max Jail Term", 30, 0, 50, 1)
}

space_component = make_space_component(
    citizen_cop_portrayal, post_process=post_process, draw_grid=False
)

chart_component = make_plot_component(
    {state.name.lower(): agent_colors[state] for state in CitizenState}
)

epstein_model = EpsteinCivilViolence()

page = SolaraViz(
    epstein_model,
    components=[space_component, chart_component],
    model_params=model_params,
    name="Epstein Civil Violence"
)

page
