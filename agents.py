"""
This file contains all the agent code for the Epstein Civil Uprising Model.
"""

from enum import Emun
import math
import mesa

"""
Class that defines the state of agents in the Epstein model
"""
class CitizenState(Enum):
    ACTIVE = 1
    QUIET = 2
    ARRESTED = 3

"""
Class that defines the agent action and movement
Agents scan neighboorhood state based on attributes defined in Citizen class
Agents move if they have no neighbors
"""
class EpsteinAgent(mesa.experimental.cell_space.CellAgent):
    def update_neighbors(self):
        """
        Looking around to see who my neighbors are
        """
        self.neighborhood = self.get_neighborhood(radius=self.vision)
        self.neighbors = self.neighborhood.agents
        self.empty_neighbors = [
            c for c in self.neighborhood if c.is_empty
        ]
    
    def move(self):
        if self.model.movement and self.empty_neighbors:
            new_pos = self.random.choice(self.empty_neighbors)
            self.move_to(new_pos)

"""
Class that defines the Agents in the Epstein model
"""
class Citizen(EpsteinAgent):
    """
    An agent of the population may or may not be in active rebellion
    Rule: if grievance - risk > threshold value, then the agent will rebel
    
    Attributes:
        hardship: agent's perceived hardship (i.e. physical or economic privation), this attribute is exogenous and drawn from U(0,1)
        regime_legitimacy: agent's perception of regime legitimacy, equal across all agents, this attribute is exogenous
        risk_aversion: exogenous, drawn from U(0,1)
        threshold: if (grievance - (risk_aversion * arrest_probability)) > threshold, agent will go/remain ACTIVE
        vision: the number of cells in each direction that an agent can inspect
        condition: can be "Quiescent" or "Active;" deterministic function of greivance and perceived risk
        grievance: deterministic function of hardship and regime_legitimacy; how aggrieved is agent at the regime?
        arrest_probability: agent's assessment of arrest probability, given rebellion
    """

    def __init__(
            self,
            model,
            regime_legitimacy,
            threshold,
            vision,
            arrest_prob_constant
    ):
      """
      Creates a new Citizen agent
      
      Args:
        model: the model to which the agent belongs
        hardship: agent's perceived hardship (i.e. physical or economic privation)
        regime_legitimacy: agent's perception of regime legitimacy, equal across all agents
        risk_aversion: exogenous, drawn from U(0,1)
        threshold: if (grievance - (risk_aversion * arrest_probability)) > threshold, agent will go/remain ACTIVE
        vision: the number of cells in each direction that an agent can inspect
        model: model instance
        """
      super().__init__(model)

      # Define the agent attributes
      self.hardship = self.random.random() # agent's perceived hardship, this is an exogenous variable derived from U(0,1)
      self.risk_aversion = self.random.random() # exogenous variable, derived from U(0,1)
      self.regime_legitimacy = regime_legitimacy # agent's perception of regime legitimacy, this is an exogenous variable, uniform across all agents  
      self.threshold = threshold # if (grievance - (risk_aversion * arrest_probability)) > threshold, the agent will go/remain in active rebellion
      self.state = CitizenState.QUIET
      self.vision = vision # the number of cells in each direction (N, E, S, W) that the agent can inspect, this is an exogenous variable
      self.jail_sentence = 0
      self.grievance = self.hardship * (1 - self.regime_legitimacy) # deterministic function of hardship and regime_legitimacy; how aggrieved is the agent at the regime?
      self.arrest_prob_constant = arrest_prob_constant # agent's assesment of arrest probability, given rebellion
      self.arrest_probability = None

      # Define the initial agent state
      self.neighborhood = []
      self.neighbors = []
      self.empty_neighbors = []

    def step(self):
        """
        Agents decide whether to rebel
        Move if applicable
        
        Note: if the agent is in jail, they are inactive and cannot rebel
        However, this still effects the model and the neighbors must be updated and estimated_arrest_probability must be updated
        """
        if self.jail_sentence:
            self.jail_sentence -= 1
            return # No other changes or movements if agent is in jail
        self.update_neighbors()
        self.update_estimated_arrest_probability()

        # Calculate the net_risk for an agent
        net_risk = self.risk_aversion * self.arrest_probability
        # If the agents is aggrivated such that grievance - net_risk > threshold
        if (self.grievance - net_risk) > self.threshold:
            # Then the agent will be active in rebellion
            self.state = CitizenState.ACTIVE
        else:
            # Otherwise, the agent will be quiet
            self.state = CitizenState.QUIET
        
        self.move()

    def update_estimated_arrest_probability(self):
        """
        Based on the ratio of cops to active rebels in the neighborhood,
        estimate the p(Arrest | agent goes active)
        """
        cops_in_vision = 0
        actives_in_vision = 1 # Agent must count self
        for neighbor in self.neighbors:
            # If there the neighbor is a cop, note that in the cops_in_vision counter
            if isinstance(neighbor, Cop):
                cops_in_vision += 1
            # If the neighbor is active, note that in the actives_in_vision counter
            elif neighbor.state == CitizenState.ACTIVE:
                actives_in_vision += 1
        
        # Calculate the arrest_probability based on literature readings
        self.arrest_probability = 1 - math.exp(
            -1 * self.arrest_prob_constant * round(cops_in_vision / actives_in_vision)
        )

"""
Class that defines Cops in the Epstein model
"""
class Cop(EpsteinAgent):
    """
    A cop for life in the model, there is no defection possible
    Rule: inspect local vision and arrest a random active agent

    Attributes:
        unique_id: unique int
        x, y: grid coordinates
        vision: number of cells in each direction that cop is able to inspect
    """
    def __init__(
            self,
            model,
            vision,
            max_jail_term
    ):
        """Creates a new Cop
        
        Args:
            x, y: grid coordinates
            vision: number of cells in each direction
            model: model instance
        """
        super().__init__(model)

        # Define the cop attributes
        self.vision = vision # the number of cells in each direction (N, E, S, W) that the agent can inspect, this is an exogenous variable
        self.max_jail_term = max_jail_term

    def step(self):
        """
        Inspect local vision and arrest a random active agent
        Move if applicable
        """
        self.update_neighbors()
        active_neighbors = []
        for agent in self.neighbors:
            if isinstance(agent, Citizen) and agent.state == CitizenState.ACTIVE:
                active_neighbors.append(agent)
        if active_neighbors:
            arrestee = self.random.choice(active_neighbors)
            arrestee.jail_setnence = self.random.randint(0, self.max_jail_term)
            arrestee.state = CitizenState.ARRESTED
        
        self.move()
