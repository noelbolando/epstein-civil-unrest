"""
This file contains all the model code for the Epstein Civil Uprising Model.
"""

import mesa
from mesa import Model

from agents import Citizen, CitizenState, Cop

"""
Class defining the Epstein Civil Violence Model
"""
class EpsteinCivilViolence(Model):
    """
    This model is based on the findings of Joshua Epstein in his 2002 paper,
    "Modeling Civil Violence: An Agent-Based Computational Approach."
    Source: https://www.pnas.org/doi/full/10.1073/pnas.092080199
    
    Args:
        height: grid height
        width: grid width
        citizen_density: approximate number of cells occupied by citizens, represented by %cells
        cop_density: approximate number of cells occupied by cops, represented by %cells
        citizen_vision: number of cells in each direction (N, E, S, and W) that citizen agents can inspect
        cop_vision: number of cells in each direction (N, E, S, and W) that cops can inspect
        legitimacy: citizen agent's perecption of regime legitimacy, equal across all citizens and represetned by (L)
        max_jail_term: maximum number of time that an agent can be in jail, represetned by (J_max)
        active_threshold: if (grievance - (risk_aversion * arrest_probability)) > threshold, citizens rebel
        arrest_prob_constant: set to ensure agents make plausible arrest probability estimates
        movement: boolean, whether agents try to move at the end of each step
        max_iters: setting a maximum number of model iterations in case model does not have a natural stopping point
    """

    def __init__(
            self,
            width=40,
            height=40,
            citizen_density=0.7,
            cop_density=0.074,
            citizen_vision=7,
            cop_vision=7,
            legiitmacy=0.8,
            max_jail_term=1000,
            active_threshold=0.1,
            arrest_prob_constant=2.3,
            movement=True,
            max_iters=1000,
            seed=None
    ):
        super().__init__(seed=seed)

        # Initiate the model attributes 
        self.movement = movement
        self.max_iters = max_iters
       
        # Initiate the model grid
        self.grid = mesa.experimental.cell_space.OrthogonalVonNeumannGrid(
            (width, height), capacity=1, torus=True, random=self.random
        )
        
        # Initiate the model reporters
        model_reporters = {
            "active": CitizenState.ACTIVE.name,
            "quiet": CitizenState.QUIET.name,
            "arrested": CitizenState.ARRESTED.name
        }
        
        # Initiate the agent reporters
        agent_reporters = {
            "jail_sentence": lambda a: getattr(a, "jail_sentence", None),
            "arrest_probability": lambda a: getattr(a, "arrest_probability", None)
        }
        
        # Initiate the data collector method for the model
        # This allows for model and agent feedback from the respective reporting parameters
        self.datacollector = mesa.DataCollector(
            model_reporters=model_reporters,
            agent_reporters=agent_reporters 
        )
        
        # Make sure the total density of a cell is not greater than 1
        if cop_density + citizen_density > 1:
            raise ValueError("Cop density + citizen density must be less than 1")
        
        for cell in self.grid.all_cells:
            klass = self.random.choices(
                [Citizen, Cop, None],
                cum_weights = [citizen_density, citizen_density + cop_density, 1]
            )[0]

            if klass == Cop:
                cop = Cop(
                    self, 
                    vision=cop_vision, 
                    max_jail_term=max_jail_term)
                cop.move_to(cell)
            elif klass == Citizen:
                citizen = Citizen(
                    self,
                    regime_legitimacy=legiitmacy,
                    threshold=active_threshold,
                    vision=citizen_vision,
                    arrest_prob_constant=arrest_prob_constant)
                citizen.move_to(cell)
        
        self.running = True
        self._update_counts()
        self.datacollector.collect(self)

    def step(self):
        """
        Advance the model by one step and collect data
        """
        self.agents.shuffle_do("step")
        self._update_counts()
        self.datacollector.collect(self)

        if self.steps > self.max_iters:
            self.running = False
    
    """Helper function for counting number of citizens in a given state"""
    def update_counts(self):
        counts = self.agents_by_type[Citizen].groupby("state").count()
        for state in CitizenState:
            setattr(self, state.name, counts.get(state,0))

